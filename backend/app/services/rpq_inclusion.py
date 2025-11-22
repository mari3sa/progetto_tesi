from typing import Set, Tuple
import re

from ..database.neo4j import get_session
from ..config import get_settings
from .rpq_syntax import parse_rpc
from ..database.manager import get_current_database_or_default


def load_rel_types() -> Set[str]:
    """
    (Per ora non usata nella validazione, ma la teniamo se serve in futuro)
    """
    s = get_settings()
    with get_session(get_current_database_or_default()) as session:
        return {
            r["type"]
            for r in session.run(
                "CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type"
            )
        }


def validate_symbols(lhs_alts, rhs_alts):
    """
    Ora controlla SOLO la sintassi (niente simboli vuoti),
    NON controlla più che le relazioni esistano nel grafo.

    Se una relazione non esiste, la relativa RPQ restituisce ∅,
    e questo produce le violazioni come da teoria delle RPC.
    """
    errors = []

    for seq in lhs_alts + rhs_alts:
        for inv, sym in seq:
            if not sym.strip():
                errors.append("Simbolo vuoto in un vincolo")

    return errors


# --------------------------------------------------------
# Espansione semplice delle parentesi nella forma:
#   X.(A|B) oppure X.(A∣B)
# → X.A∣X.B
# (niente annidamento complesso, ma sufficiente per C2)
# --------------------------------------------------------
def _expand_simple_parentheses(constraint_str: str) -> str:
    """
    Esempio:
      'C2=child_of.(brother_of∣sister_of)⊆nephew_of∣niece_of'
    diventa
      'C2=child_of.brother_of∣child_of.sister_of⊆nephew_of∣niece_of'
    """
    s = constraint_str

    # normalizza l'operatore di unione a '∣'
    s = s.replace("|", "∣")

    # pattern: prefisso (eventualmente con altri '.') seguito da .(A∣B)
    pattern = re.compile(
        r'([\w_]+(?:\.[\w_]+)*)\.\(([\w_]+)\s*∣\s*([\w_]+)\)'
    )

    while True:
        m = pattern.search(s)
        if not m:
            break

        prefix = m.group(1)  # es. "child_of" o "r1.r2"
        opt1 = m.group(2)
        opt2 = m.group(3)

        replacement = f"{prefix}.{opt1}∣{prefix}.{opt2}"
        s = s[:m.start()] + replacement + s[m.end():]

    return s


def pairs_for_sequence(seq):
    """
    Ritorna tutte le coppie (u,v) tali che esiste un cammino
    u --R1--> x1 --R2--> x2 ... --Rn--> v
    per la sequenza 'seq'.

    seq = [(inv, 'rel1'), (inv, 'rel2'), ...]
    """
    db = get_current_database_or_default()

    # costruzione del pattern MATCH
    pattern = "(n0)"
    for i, (inv, rel) in enumerate(seq):
        if inv:
            pattern += f"<-[:`{rel}`]-(n{i+1})"
        else:
            pattern += f"-[:`{rel}`]->(n{i+1})"

    query_text = f"""
        MATCH {pattern}
        RETURN DISTINCT id(n0) AS u, id(n{len(seq)}) AS v
    """

    out: Set[Tuple[int, int]] = set()
    with get_session(db) as s:
        for row in s.run(query_text):
            out.add((row["u"], row["v"]))

    return out


def pairs_for_alts(alts) -> Set[Tuple[int, int]]:
    out: Set[Tuple[int, int]] = set()
    for seq in alts:
        out |= pairs_for_sequence(seq)
    return out


def check_inclusion(constraint_str: str) -> dict:
    """
    Endpoint logico per /api/rpq/check

    constraint_str: stringa tipo
      "C2=child_of.(brother_of∣sister_of)⊆nephew_of∣niece_of"
    """
    # 0) espandi eventuali parentesi semplici
    expanded = _expand_simple_parentheses(constraint_str)

    # 1) parsing rigoroso RPC
    name, lhs, rhs = parse_rpc(expanded)  # se non è RPC, ValueError

    # 2) validazione sintattica dei simboli
    schema_errors = validate_symbols(lhs, rhs)
    if schema_errors:
        return {
            "ok": False,
            "type": "schema_validation",
            "errors": schema_errors,
            "name": name,
        }

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
