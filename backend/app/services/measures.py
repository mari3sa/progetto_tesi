"""
Funzioni per il calcolo delle misure di inconsistenza derivate dai vincoli RPQ.

Il modulo analizza una lista di vincoli (nella sintassi RPC), calcola tutte
le coppie problematiche u→v presenti nel grafo e misura diverse forme di
inconsistenza strutturale:
- violazioni dei vincoli,
- insiemi minimali di archi problematici (MIMS),
- percorsi testimoni u→v,
- misure standard (I_B, I_C, I_P, I_M, I_E, …).

Il calcolo avviene interrogando direttamente il database attivo, senza
presupporre che il grafo stia interamente in memoria.
"""

from typing import List, Dict, Any, Set, Tuple

from .rpq_syntax import parse_rpc
from .rpq_inclusion import (
    validate_symbols,
    pairs_for_sequence,
    _expand_simple_parentheses,
)
from ..database.neo4j import get_session
from ..database.manager import get_current_database_or_default



# Helper: trova 1 percorso testimone u -> v per una sequenza RPQ
def one_witness_path_for_sequence(
    seq, u_id: int, v_id: int
) -> List[Tuple[int, int, str]]:
    """
    Restituisce un cammino u→…→v che rispetta esattamente la sequenza 'seq'.
    Se non esiste, ritorna [].
    """

    # Per semplicità non gestiamo inverse
    if any(inv for inv, _ in seq):
        return []

    db = get_current_database_or_default()

    with get_session(db) as s:
        parts = ["(n0)"]
        for i, (_, rel) in enumerate(seq):
            parts.append(f"-[:`{rel}`]->(n{i+1})")
        pattern = "".join(parts)

        ret = ", ".join([f"id(n{i}) AS n{i}" for i in range(len(seq) + 1)])

        query = f"""
            MATCH {pattern}
            WHERE id(n0) = $u AND id(n{len(seq)}) = $v
            RETURN {ret} LIMIT 1
        """

        row = s.run(query, u=u_id, v=v_id).single()
        if not row:
            return []

        # Ricostruzione lista archi del cammino testimone
        return [
            (row[f"n{i}"], row[f"n{i+1}"], rel)
            for i, (_, rel) in enumerate(seq)
        ]


# Funzione principale: calcola tutte le misure di inconsistenza
def compute_measures(constraints: List[str], requested_measures: List[str]) -> Dict[str, Any]:
    """
    Calcola SOLO le misure richieste e nel modo più efficiente possibile.
    Le query a Neo4j vengono ridotte drasticamente usando caching logico
    e evitando calcoli superflui.
    """

    requested = set(requested_measures or [])

    # 1) ANALISI DEI VINCOLI: coppie problematiche per ogni vincolo
    all_problem_pairs: Set[Tuple[int, int]] = set()
    violated_count = 0
    per_constraint = []

    # Mappa fondamentale: quali sequenze LHS hanno generato quali violazioni
    # (u,v) → [seq1, seq2, ...]
    violations_source = {}

    need_pairs = any(m in requested for m in [
        "problematic_pairs", "minimal_problematic_graphs", "minimal_problematic_paths",
        "problematic_edges", "problematic_labels", "problematic_vertices",
        "I_E_minus", "I_E_plus", "I_V_minus"
    ])

    for raw in constraints:
        raw_expanded = _expand_simple_parentheses(raw)
        name, lhs_alts, rhs_alts = parse_rpc(raw_expanded)

        # Errore nei simboli → vincolo violato
        errors = validate_symbols(lhs_alts, rhs_alts)
        if errors:
            violated_count += 1
            per_constraint.append({
                "name": name,
                "ok": False,
                "type": "schema_validation",
                "errors": errors,
            })
            continue

        # Calcolo coppie raggiungibili LHS e RHS
        lhs_pairs = set()
        for seq in lhs_alts:
            lhs_pairs |= pairs_for_sequence(seq)

        rhs_pairs = set()
        for seq in rhs_alts:
            rhs_pairs |= pairs_for_sequence(seq)

        violations = lhs_pairs - rhs_pairs
        ok = len(violations) == 0

        if not ok:
            violated_count += 1

            if need_pairs:
                all_problem_pairs |= violations

                #Salviamo SOLO le sequenze LHS che hanno provocato la violazione
                for (u, v) in violations:
                    violations_source.setdefault((u, v), []).extend(lhs_alts)

        per_constraint.append({
            "name": name,
            "ok": ok,
            "lhs_pairs": len(lhs_pairs),
            "rhs_pairs": len(rhs_pairs),
            "violations_count": len(violations),
        })

    # 2) MISURE SEMPLICI (non richiedono percorsi)
    summary = {}

    if "mu_drastic" in requested:
        summary["mu_drastic"] = 1 if violated_count > 0 else 0

    if "mu_violated_constraints" in requested:
        summary["mu_violated_constraints"] = violated_count

    if "problematic_pairs" in requested:
        summary["problematic_pairs"] = len(all_problem_pairs)

    # Se sono richieste solo misure semplici → STOP qui
    if requested <= {"mu_drastic", "mu_violated_constraints", "problematic_pairs"}:
        return {
            "summary": summary,
            "details": {"per_constraint": per_constraint}
        }

    # 3) CALCOLO WITNESS PATH (solo per le coppie e sequenze LHS rilevanti)
    all_witness_paths = []
    for (u, v), seqs in violations_source.items():
        for seq in seqs:
            path = one_witness_path_for_sequence(seq, u, v)
            if path:
                all_witness_paths.append(path)
                break  # basta un testimone per questa coppia

    # 4) MIMS (minimal problematic graphs)
    if "minimal_problematic_graphs" in requested or "I_E_minus" in requested:

        path_sets = [frozenset(p) for p in all_witness_paths if p]
        minimal_sets = []

        for i, S in enumerate(path_sets):
            if not any(T < S for j, T in enumerate(path_sets) if i != j):
                minimal_sets.append(S)

        if "minimal_problematic_graphs" in requested:
            summary["minimal_problematic_graphs"] = len(minimal_sets)

        if "I_E_minus" in requested:
            summary["I_E_minus"] = len(minimal_sets)

    # 5) Minimal problematic paths I_S(G)
    if "minimal_problematic_paths" in requested:

        path_list = [tuple(p) for p in all_witness_paths]
        minimal_paths = []

        for i, P in enumerate(path_list):
            setP = set(P)
            smaller_exists = any(
                set(Q) < setP
                for j, Q in enumerate(path_list)
                if i != j
            )
            if not smaller_exists:
                minimal_paths.append(P)

        summary["minimal_problematic_paths"] = len(minimal_paths)

    # 6) ARCHI, LABEL, NODI PROBLEMATICI
    prob_edges = set()
    for p in all_witness_paths:
        prob_edges |= set(p)

    if "problematic_edges" in requested:
        summary["problematic_edges"] = len(prob_edges)

    if "problematic_labels" in requested:
        summary["problematic_labels"] = len({lab for (_, _, lab) in prob_edges})

    if "problematic_vertices" in requested:
        vertices = {u for (u, _, _) in prob_edges} | {v for (_, v, _) in prob_edges}
        summary["problematic_vertices"] = len(vertices)

    # 7) I(E+): archi da aggiungere
    if "I_E_plus" in requested:
        summary["I_E_plus"] = len(all_problem_pairs)

    # 8) I(V−): vertex cover approssimato
    if "I_V_minus" in requested:

        freq = {}
        for u, v in all_problem_pairs:
            freq[u] = freq.get(u, 0) + 1
            freq[v] = freq.get(v, 0) + 1

        pairs_left = set(all_problem_pairs)
        removed = set()

        while pairs_left and freq:
            v_star = max(freq, key=freq.get)
            removed.add(v_star)

            pairs_left = {(a, b) for (a, b) in pairs_left if a != v_star and b != v_star}

            freq = {}
            for a, b in pairs_left:
                freq[a] = freq.get(a, 0) + 1
                freq[b] = freq.get(b, 0) + 1

        summary["I_V_minus"] = len(removed)

    # OUTPUT FINALE
    return {
        "summary": summary,
        "details": {"per_constraint": per_constraint}
    }
