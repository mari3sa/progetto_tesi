"""
Calcolo ottimizzato delle misure RPC su grafi Neo4j.

Include:
- fast-path per mu_drastic, mu_violated_constraints e problematic_pairs
- slow-path usato solo se richiesto
- recupero cammini testimone solo se necessario
"""

from typing import List, Dict, Any, Set, Tuple, Optional

from .rpq_syntax import parse_rpc
from .rpq_inclusion import (
    validate_symbols,
    pairs_for_sequence,
    _expand_simple_parentheses,
)
from ..database.neo4j import get_session
from ..database.manager import get_current_database_or_default


#  FAST CHECK: trova una violazione SENZA calcolare tutte le coppie
def fast_violation(lhs_alts, rhs_alts) -> Tuple[bool, Set[Tuple[int, int]]]:
    """
    Restituisce appena trova una violazione (super veloce).
    Restituisce:
        (has_violation, alcune_coppie_violanti)
    """

    db = get_current_database_or_default()
    violations = set()

    with get_session(db) as s:

        for lhs in lhs_alts:

            # Pattern corretto lineare: (n0)-[:R1]->(n1)-[:R2]->(n2)...
            parts = ["(n0)"]
            for i, (_, rel) in enumerate(lhs):
                parts.append(f"-[:`{rel}`]->(n{i+1})")
            lhs_pattern = "".join(parts)
            last = len(lhs)

            # Se RHS è vuoto, tutto è violazione
            if not rhs_alts:
                q = f"MATCH {lhs_pattern} RETURN id(n0) AS u, id(n{last}) AS v LIMIT 20"
                rows = s.run(q).data()
                if rows:
                    for r in rows:
                        violations.add((r["u"], r["v"]))
                    return True, violations
                continue

            # EXISTS per RHS
            exists_list = []
            for rhs in rhs_alts:
                parts_rhs = ["(m0)"]
                for j, (_, rel) in enumerate(rhs):
                    parts_rhs.append(f"-[:`{rel}`]->(m{j+1})")
                rhs_pattern = "".join(parts_rhs)
                last_rhs = len(rhs)

                exists_list.append(
                    f"EXISTS {{ MATCH {rhs_pattern} "
                    f"WHERE id(m0)=id(n0) AND id(m{last_rhs})=id(n{last}) }}"
                )

            rhs_cond = " OR ".join(exists_list)

            query = f"""
            MATCH {lhs_pattern}
            WHERE NOT ({rhs_cond})
            RETURN id(n0) AS u, id(n{last}) AS v
            LIMIT 20
            """

            rows = s.run(query).data()
            if rows:
                for r in rows:
                    violations.add((r["u"], r["v"]))
                return True, violations

    return False, violations


#  CAMMINO TESTIMONE 
def one_witness_path_for_sequence(seq, u_id: int, v_id: int):
    if any(inv for inv, _ in seq):
        return []

    db = get_current_database_or_default()

    with get_session(db) as s:
        parts = ["(n0)"]
        for i, (_, rel) in enumerate(seq):
            parts.append(f"-[:`{rel}`]->(n{i+1})")
        pattern = "".join(parts)

        ret = ", ".join(f"id(n{i}) AS n{i}" for i in range(len(seq) + 1))

        q = f"""
            MATCH {pattern}
            WHERE id(n0)=$u AND id(n{len(seq)})=$v
            RETURN {ret} LIMIT 1
        """

        row = s.run(q, u=u_id, v=v_id).single()
        if not row:
            return []

        return [
            (row[f"n{i}"], row[f"n{i+1}"], rel)
            for i, (_, rel) in enumerate(seq)
        ]


#  FUNZIONE PRINCIPALE (fast + slow)
def compute_measures(
    constraints: List[str],
    requested_measures: Optional[List[str]] = None,
) -> Dict[str, Any]:

    if requested_measures is None:
        requested_measures = [
            "mu_drastic",
            "mu_violated_constraints",
            "problematic_pairs",
            "minimal_problematic_graphs",
            "minimal_problematic_paths",
            "problematic_edges",
            "problematic_labels",
            "problematic_vertices",
            "I_E_minus",
            "I_E_plus",
            "I_V_minus",
        ]

    req = set(requested_measures)
    summary = {}
    per_constraint = []

    all_lhs = []
    all_rhs = []

    violated_constraints = 0
    fast_pairs = set()

    # 1) FAST CHECK per ogni vincolo

    for raw in constraints:
        expanded = _expand_simple_parentheses(raw)
        name, lhs, rhs = parse_rpc(expanded)

        errors = validate_symbols(lhs, rhs)
        if errors:
            violated_constraints += 1
            per_constraint.append(
                {"name": name, "ok": False, "type": "schema_validation", "errors": errors}
            )
            continue

        need_fast = req & {"mu_drastic", "mu_violated_constraints", "problematic_pairs"}

        if need_fast:
            has_violation, pairs_here = fast_violation(lhs, rhs)
        else:
            has_violation, pairs_here = False, set()

        if has_violation:
            violated_constraints += 1
            fast_pairs |= pairs_here

        per_constraint.append(
            dict(
                name=name,
                ok=not has_violation,
                lhs_pairs="FAST",
                rhs_pairs="FAST",
                violations_count=len(pairs_here),
            )
        )

        all_lhs.extend(lhs)
        all_rhs.extend(rhs)

    # 2) MISURE BASE VELOCISSIME

    if "mu_drastic" in req:
        summary["mu_drastic"] = 1 if violated_constraints > 0 else 0

    if "mu_violated_constraints" in req:
        summary["mu_violated_constraints"] = violated_constraints

    if "problematic_pairs" in req:
        summary["problematic_pairs"] = len(fast_pairs)

    # FAST EXIT → se l’utente vuole solo misure base
    if req <= {"mu_drastic", "mu_violated_constraints", "problematic_pairs"}:
        return {
            "summary": summary,
            "details": {
                "per_constraint": per_constraint,
                "pairs": list(map(list, fast_pairs)),
                "MIMS": [],
                "minimal_paths": [],
            }
        }

    # 3) SLOW PATH — calcolo TUTTI i cammini LHS e RHS

    all_pairs_LHS = set()
    all_pairs_RHS = set()

    for seq in all_lhs:
        all_pairs_LHS |= pairs_for_sequence(seq)
    for seq in all_rhs:
        all_pairs_RHS |= pairs_for_sequence(seq)

    all_problem_pairs = all_pairs_LHS - all_pairs_RHS

    # 4) Cammini testimone (solo se servono misure avanzate)

    need_paths = req & {
        "minimal_problematic_graphs",
        "minimal_problematic_paths",
        "problematic_edges",
        "problematic_labels",
        "problematic_vertices",
        "I_E_minus",
    }

    witness_paths = []

    if need_paths:
        for (u, v) in all_problem_pairs:
            for seq in all_lhs:
                p = one_witness_path_for_sequence(seq, u, v)
                if p:
                    witness_paths.append(p)
                    break

    # 5) Misure derivate

    prob_edges = set()
    prob_labels = set()
    prob_vertices = set()

    for p in witness_paths:
        for u, v, rel in p:
            prob_edges.add((u, v, rel))
            prob_labels.add(rel)
            prob_vertices.add(u)
            prob_vertices.add(v)

    if "problematic_edges" in req:
        summary["problematic_edges"] = len(prob_edges)

    if "problematic_labels" in req:
        summary["problematic_labels"] = len(prob_labels)

    if "problematic_vertices" in req:
        summary["problematic_vertices"] = len(prob_vertices)

    # 6) Percorsi problematici minimali (I_S)

    minimal_paths = []

    if "minimal_problematic_paths" in req:
        plist = [tuple(p) for p in witness_paths]
        for i, P in enumerate(plist):
            setP = set(P)
            if all(not (set(plist[j]).issubset(setP) and len(plist[j]) < len(P))
                   for j in range(len(plist)) if j != i):
                minimal_paths.append(P)

        summary["minimal_problematic_paths"] = len(minimal_paths)

    # 7) MIMS (I_M)

    minimal_sets = []

    if "minimal_problematic_graphs" in req or "I_E_minus" in req:
        path_sets = [frozenset(p) for p in witness_paths]
        for i, S in enumerate(path_sets):
            if all(not (path_sets[j] < S) for j in range(len(path_sets)) if j != i):
                minimal_sets.append(S)

        if "minimal_problematic_graphs" in req:
            summary["minimal_problemmatic_graphs"] = len(minimal_sets)

    # 8) Correttive
    

    if "I_E_minus" in req:
        summary["I_E_minus"] = len(minimal_sets)

    if "I_E_plus" in req:
        summary["I_E_plus"] = len(all_problem_pairs)

    if "I_V_minus" in req:
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


    return {
        "summary": summary,
        "details": {
            "per_constraint": per_constraint,
            "pairs": list(map(list, all_problem_pairs)),
            "MIMS": [list(m) for m in minimal_sets],
            "minimal_paths": [list(p) for p in minimal_paths],
        }
    }
