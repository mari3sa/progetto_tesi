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
def compute_measures(constraints: List[str]) -> Dict[str, Any]:
    """
    Esegue il calcolo completo delle misure a partire da una lista
    di vincoli RPC.
    Ritorna sia il riepilogo globale sia i dettagli per singolo vincolo.
    """

    db = get_current_database_or_default()

    # Insiemi globali per tutte le violazioni trovate
    all_problem_pairs: Set[Tuple[int, int]] = set()
    all_witness_paths: List[List[Tuple[int, int, str]]] = []  # TUTTI i cammini testimoni

    violated_count = 0
    per_constraint = []

    # Analisi di ogni vincolo RPC
    for raw in constraints:
        # Espansione di parentesi semplici per uniformare il parsing
        raw_expanded = _expand_simple_parentheses(raw)

        name, lhs_alts, rhs_alts = parse_rpc(raw_expanded)

        # verifica simboli (solo sintassi)
        errors = validate_symbols(lhs_alts, rhs_alts)
        if errors:
            per_constraint.append(
                {
                    "name": name,
                    "ok": False,
                    "type": "schema_validation",
                    "errors": errors,
                }
            )
            continue

        # Calcolo coppie LHS e RHS come unioni delle alternative
        lhs_pairs: Set[Tuple[int, int]] = set()
        for seq in lhs_alts:
            lhs_pairs |= pairs_for_sequence(seq)

        rhs_pairs: Set[Tuple[int, int]] = set()
        for seq in rhs_alts:
            rhs_pairs |= pairs_for_sequence(seq)

        violations = lhs_pairs - rhs_pairs
        ok = len(violations) == 0

        if not ok:
            violated_count += 1
            all_problem_pairs |= violations

            # Per ogni coppia violata, estrae un percorso testimone
            for (u, v) in violations:
                for seq in lhs_alts:
                    path = one_witness_path_for_sequence(seq, u, v)
                    if path:
                        all_witness_paths.append(path)
                        break

        per_constraint.append(
            {
                "name": name,
                "ok": ok,
                "lhs_pairs": len(lhs_pairs),
                "rhs_pairs": len(rhs_pairs),
                "violations_count": len(violations),
            }
        )

    # COSTRUZIONE DEI MIMS (sottografi minimalmente inconsistenti)
    path_sets = [frozenset(p) for p in all_witness_paths if p]

    minimal_sets: List[Set[Tuple[int, int, str]]] = []
    for i, S in enumerate(path_sets):
        # S è minimale se nessun T più piccolo è sottoinsieme di S
        is_minimal = True
        for j, T in enumerate(path_sets):
            if i == j:
                continue
            if T < S:  # T è sottoinsieme proprio di S
                is_minimal = False
                break
        if is_minimal:
            minimal_sets.append(S)

    
    # COSTRUZIONE I_S(G): percorsi problematici minimali
    path_list = [tuple(p) for p in all_witness_paths]

    minimal_paths = []
    for i, P in enumerate(path_list):
        setP = set(P)
        is_minimal = True
        for j, Q in enumerate(path_list):
            if i == j:
                continue
            setQ = set(Q)
            if len(setQ) < len(setP) and setQ.issubset(setP):
                is_minimal = False
                break
        if is_minimal:
            minimal_paths.append(P)

    I_S = len(minimal_paths)  # I_S(G)

    
    # ARCHI / ETICHETTE / NODI PROBLEMATICI
    prob_edges: Set[Tuple[int, int, str]] = set()
    for path in all_witness_paths:
        prob_edges |= set(path)

    prob_labels: Set[str] = {lab for (_, _, lab) in prob_edges}

    prob_vertices: Set[int] = set()
    for (u, v, _) in prob_edges:
        prob_vertices.add(u)
        prob_vertices.add(v)

    # MISURE STANDARD 
    mu_d = 1 if violated_count > 0 else 0          # I_B(G)
    mu_vc = violated_count                         # I_C(G)
    P = len(all_problem_pairs)                     # I_P(G)
    I_M = len(minimal_sets)                        # I_M(G) = |MIMS(G)|
    E_p = len(prob_edges)                          # I_E(G)
    L_p = len(prob_labels)                         # I_L(G)
    V_p = len(prob_vertices)                       # I_V(G)

    # MISURE AGGIUNTIVE: I(E-), I(E+), I(V-)
    

    #I(E-)
    I_E_minus = I_M

    #I(E+) = numero coppie problematiche (una correzione per ogni coppia)
    I_E_plus = P

    #I(V-) = cover di vertici (approssimata greedy)
    freq = {}
    for u, v in all_problem_pairs:
        freq[u] = freq.get(u, 0) + 1
        freq[v] = freq.get(v, 0) + 1

    pairs_left = set(all_problem_pairs)
    removed_vertices: Set[int] = set()

    # Scelta greedy del vertice più frequente
    while pairs_left:
        v_star = max(freq, key=freq.get)
        removed_vertices.add(v_star)

        pairs_left = {(a, b) for (a, b) in pairs_left if a != v_star and b != v_star}

        freq = {}
        for a, b in pairs_left:
            freq[a] = freq.get(a, 0) + 1
            freq[b] = freq.get(b, 0) + 1

        if not freq:
            break

    I_V_minus = len(removed_vertices)

    
    #RISULTATO
    return {
        "summary": {
            "mu_drastic": mu_d,                      # I_B(G)
            "mu_violated_constraints": mu_vc,        # I_C(G)
            "problematic_pairs": P,                  # I_P(G)
            "minimal_problematic_graphs": I_M,       # I_M(G)
            "minimal_problematic_paths": I_S,        # I_S(G)
            "problematic_edges": E_p,                # I_E(G)
            "problematic_labels": L_p,               # I_L(G)
            "problematic_vertices": V_p,             # I_V(G)
            "I_E_minus": I_E_minus,
            "I_E_plus": I_E_plus,
            "I_V_minus": I_V_minus,
        },
        "details": {
            "per_constraint": per_constraint,
            "pairs": list(map(list, all_problem_pairs)),
            "MIMS": [list(m) for m in minimal_sets],
            "minimal_paths": [list(p) for p in minimal_paths],
        },
    }
