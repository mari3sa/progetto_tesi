# app/services/measures.py

from typing import List, Dict, Any, Set, Tuple

from .rpq_syntax import parse_rpc
from .rpq_inclusion import (
    validate_symbols,
    pairs_for_sequence,
    _expand_simple_parentheses,
)
from ..database.neo4j import get_session
from ..database.manager import get_current_database_or_default


# ---------------------------------------------------------------
# Helper: trova 1 percorso testimone u -> v per una sequenza RPQ
# ---------------------------------------------------------------
def one_witness_path_for_sequence(
    seq, u_id: int, v_id: int
) -> List[Tuple[int, int, str]]:
    """
    Ritorna una lista di archi (u,v,label) che formano un cammino u->...->v
    per la sequenza di relazioni 'seq'. Se non trovato, ritorna [].
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

        # ricostruisci archi (n_i, n_{i+1}, label_i)
        return [
            (row[f"n{i}"], row[f"n{i+1}"], rel)
            for i, (_, rel) in enumerate(seq)
        ]


# ---------------------------------------------------------------
# Funzione principale: calcola tutte le misure di inconsistenza
# ---------------------------------------------------------------
def compute_measures(constraints: List[str]) -> Dict[str, Any]:
    """
    constraints = lista di stringhe RPC, ad es.:

      "C1=child_of⊆son_of∣daughter_of"
      "C2=child_of.(brother_of∣sister_of)⊆nephew_of∣niece_of"
      "C3=child_of.child_of⊆grandson_of∣granddaughter_of"
      "C4=son_of.child_of⊆grandson_of"

    Ritorna:
      - summary: tutte le misure globali
      - details: info per vincolo + qualche path
    """

    db = get_current_database_or_default()

    # insiemi globali
    all_problem_pairs: Set[Tuple[int, int]] = set()
    all_witness_paths: List[List[Tuple[int, int, str]]] = []  # TUTTI i cammini testimoni

    violated_count = 0
    per_constraint = []

    # ===============================================================
    # PROCESSA TUTTI I VINCOLI
    # ===============================================================
    for raw in constraints:
        # espandi eventuali parentesi semplici
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

        # calcola LHS e RHS (unione delle alternative)
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

            # estrai UN percorso testimone per ciascuna coppia violata
            for (u, v) in violations:
                for seq in lhs_alts:
                    path = one_witness_path_for_sequence(seq, u, v)
                    if path:
                        # lo teniamo sempre (serve per I_E(G))
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

    # ===============================================================
    # COSTRUZIONE DEI MIMS (sottografi minimalmente inconsistenti)
    # ===============================================================
    # ogni path → insieme di archi
    path_sets = [frozenset(p) for p in all_witness_paths if p]

    minimal_sets: List[Set[Tuple[int, int, str]]] = []
    for i, S in enumerate(path_sets):
        # S è minimale se NON esiste un T (j != i) con T ⊂ S
        is_minimal = True
        for j, T in enumerate(path_sets):
            if i == j:
                continue
            if T < S:  # T è sottoinsieme proprio di S
                is_minimal = False
                break
        if is_minimal:
            minimal_sets.append(S)

    # ===============================================================
    # COSTRUZIONE I_S(G): percorsi problematici minimali
    # ===============================================================
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

    # ===============================================================
    # ARCHI / ETICHETTE / NODI PROBLEMATICI
    # ===============================================================
    prob_edges: Set[Tuple[int, int, str]] = set()
    for path in all_witness_paths:
        prob_edges |= set(path)

    prob_labels: Set[str] = {lab for (_, _, lab) in prob_edges}

    prob_vertices: Set[int] = set()
    for (u, v, _) in prob_edges:
        prob_vertices.add(u)
        prob_vertices.add(v)

    # ===============================================================
    # MISURE STANDARD (come nel paper)
    # ===============================================================
    mu_d = 1 if violated_count > 0 else 0          # I_B(G)
    mu_vc = violated_count                         # I_C(G)
    P = len(all_problem_pairs)                     # I_P(G)
    I_M = len(minimal_sets)                        # I_M(G) = |MIMS(G)|
    E_p = len(prob_edges)                          # I_E(G)
    L_p = len(prob_labels)                         # I_L(G)
    V_p = len(prob_vertices)                       # I_V(G)

    # ===============================================================
    # MISURE AGGIUNTIVE: I(E-), I(E+), I(V-)
    # ===============================================================

    # 🔹 I(E-) (come PRIMA, uguale a I_M(G) nei tuoi esempi)
    I_E_minus = I_M

    # 🔹 I(E+) = numero coppie problematiche (una correzione per ogni coppia)
    I_E_plus = P

    # 🔹 I(V-) = cover di vertici (approssimata greedy)
    freq = {}
    for u, v in all_problem_pairs:
        freq[u] = freq.get(u, 0) + 1
        freq[v] = freq.get(v, 0) + 1

    pairs_left = set(all_problem_pairs)
    removed_vertices: Set[int] = set()

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

    # ===============================================================
    # RITORNO RISULTATO
    # ===============================================================
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
