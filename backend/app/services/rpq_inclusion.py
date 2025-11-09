from typing import Set, Tuple
from ..database.neo4j import get_session
from ..config import get_settings
from .rpq_syntax import parse_rpc  
from ..database.manager import get_current_database_or_default


def load_rel_types() -> Set[str]:
    s = get_settings()
    with get_session(get_current_database_or_default()) as session:
        return { r["type"] for r in session.run(
            "CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type") }

def validate_symbols(lhs, rhs) -> list[str]:
    rels = load_rel_types()
    errors = []
    def check_side(side, alts):
        for seq in alts:
            for inv, rel in seq:
                if rel not in rels:
                    errors.append(f"{side}: relazione '{rel}' non presente nel grafo")
                if inv:
                    # semantica dell’inverso non implementata nella fase MATCH lineare:
                    errors.append(f"{side}: uso di relazione inversa '^ {rel}' non ancora supportato nella valutazione")
    check_side("LHS", lhs)
    check_side("RHS", rhs)
    return errors

def pairs_for_sequence(seq) -> Set[Tuple[int,int]]:
    """
    seq = [(inv, 'child_of'), (inv, 'child_of'), ...]
    Per ora rifiutiamo 'inv=True' (vedi validate_symbols).
    """
    s = get_settings()
    with get_session(get_current_database_or_default()) as session:
        nodes = [f"n{i}" for i in range(len(seq)+1)]
        steps = []
        for i, (inv, rel) in enumerate(seq):
            if inv:
                # qui potresti invertire la direzione, ma al momento non lo supportiamo
                raise ValueError("Relazioni inverse non supportate nella valutazione")
            steps.append(f"({nodes[i]})-[:`{rel}`]->({nodes[i+1]})")
        pattern = "-".join(steps)
        cypher = f"MATCH {pattern} RETURN id({nodes[0]}) AS u, id({nodes[-1]}) AS v"
        return { (rec["u"], rec["v"]) for rec in session.run(cypher) }

def pairs_for_alts(alts) -> Set[Tuple[int,int]]:
    out = set()
    for seq in alts:
        out |= pairs_for_sequence(seq)
    return out

def check_inclusion(constraint_str: str) -> dict:
    # 1) parsing rigoroso RPC
    name, lhs, rhs = parse_rpc(constraint_str)  # <-- se non è RPC, ValueError

    # 2) validazione simboli contro schema DB
    schema_errors = validate_symbols(lhs, rhs)
    if schema_errors:
        return {"ok": False, "type": "schema_validation", "errors": schema_errors, "name": name}

    # 3) valutazione insiemistica LHS⊆RHS
    lhs_pairs = pairs_for_alts(lhs)
    rhs_pairs = pairs_for_alts(rhs)
    violations = sorted(list(lhs_pairs - rhs_pairs))

    return {
        "ok": len(violations) == 0,
        "name": name,
        "lhs_pairs": len(lhs_pairs),
        "rhs_pairs": len(rhs_pairs),
        "violations": violations[:200],
        "violations_count": len(violations),
    }
