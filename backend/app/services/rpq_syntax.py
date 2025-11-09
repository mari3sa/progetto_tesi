import re
from typing import List, Tuple

# Accettiamo sia il simbolo unicode '⊆' sia ASCII '<='
SUBSET_OPS = ["⊆", "<="]

# token relazione: lettere, numeri, underscore, inizia per lettera/underscore
REL_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# --------- Tokenizer ---------
def tokenize(expr: str) -> List[str]:
    # normalizza spazi e sostituisce '|' se usato al posto di '∣'
    s = expr.strip().replace("|", "∣")
    tokens: List[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in [".", "∣", "(", ")", "^", "*", "+"]:
            tokens.append(c)
            i += 1
            continue
        # relazione (es: child_of)
        m = REL_RE.match(s, i)
        if m:
            tokens.append(m.group(0))
            i = m.end()
            continue
        # operatore di inclusione
        if any(s.startswith(op, i) for op in SUBSET_OPS):
            for op in SUBSET_OPS:
                if s.startswith(op, i):
                    tokens.append(op)
                    i += len(op)
                    break
            continue
        raise ValueError(f"Token non valido vicino a: '{s[i:i+10]}'")
    return tokens

# --------- Parser RPQ (espressione a → (concatenazione '.') e (alternativa '∣'); opzionale '()') ---------
# Grammar (semplice):
#   RPQ      := ALT ('∣' ALT)*
#   ALT      := SEQ ('.' SEQ)*
#   SEQ      := ( '^'? REL ) | '(' RPQ ')'
#   REL      := [A-Za-z_][A-Za-z0-9_]*
# (Estensioni come '*','+' le rifiutiamo per ora, oppure si possono abilitare facilmente)

class Parser:
    def __init__(self, tokens: List[str]):
        self.toks = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, t: str) -> None:
        if self.peek() == t:
            self.i += 1
        else:
            raise ValueError(f"Aspettavo '{t}' ma ho trovato '{self.peek()}'")

    def parse_rel(self) -> Tuple[bool, str]:
        inv = False
        if self.peek() == "^":
            inv = True
            self.eat("^")
        tok = self.peek()
        if tok and REL_RE.fullmatch(tok):
            self.eat(tok)
            return inv, tok
        raise ValueError("Atteso un nome di relazione")

    def parse_seq(self) -> List[Tuple[bool, str]]:
        if self.peek() == "(":
            self.eat("(")
            alts = self.parse_rpq()
            self.eat(")")
            # per semplicità: non permettiamo quantificatori qui
            # appiattiamo: scegliamo di rappresentare una seq che contiene un “sotto-RPQ”
            # ma per la semantica attuale (espansione in Cypher lineare) è meglio vietarlo
            # quindi rigettiamo parentesi per ora:
            raise ValueError("Le parentesi sono per ora non supportate")
        inv, r = self.parse_rel()
        return [(inv, r)]

    def parse_alt(self) -> List[List[Tuple[bool, str]]]:
        # ritorna una lista di SEQ concatenate: [[(inv,rel), ...], ...]
        seqs: List[List[Tuple[bool, str]]] = []
        seqs.append(self.parse_seq())
        while self.peek() == ".":
            self.eat(".")
            seqs.append(self.parse_seq())
        return seqs

    def parse_rpq(self) -> List[List[Tuple[bool, str]]]:
        # lista di alternative; ciascuna alternativa è una lista di SEQ
        alts: List[List[Tuple[bool, str]]] = []
        alts.extend(self.parse_alt())
        while self.peek() == "∣":
            self.eat("∣")
            alts.extend(self.parse_alt())
        return alts

def parse_rpc(raw: str) -> tuple[str | None, List[List[Tuple[bool,str]]], List[List[Tuple[bool,str]]]]:
    """
    Restituisce (nome, LHS, RHS) se la stringa è un RPC valido 'name?= RPQ ⊆ RPQ'.
    LHS/RHS sono liste di 'sequenze' (ogni sequenza = lista di (inversa?, relazione)).
    """
    s = raw.strip()
    name = None
    if "=" in s:
        name, s = s.split("=", 1)
        name = name.strip()
    toks = tokenize(s)
    # split su operatore di inclusione
    if not any(op in toks for op in SUBSET_OPS):
        raise ValueError("Vincolo privo dell'operatore di inclusione ⊆ o <=")
    # trova indice operatore
    k = None
    for idx, t in enumerate(toks):
        if t in SUBSET_OPS:
            k = idx
            break
    if k in (None, 0, len(toks)-1):
        raise ValueError("Forma RPC non valida (LHS ⊆ RHS)")

    pL = Parser(toks[:k])
    lhs = pL.parse_rpq()
    if pL.peek() is not None:
        raise ValueError("Token extra nel LHS")

    pR = Parser(toks[k+1:])
    rhs = pR.parse_rpq()
    if pR.peek() is not None:
        raise ValueError("Token extra nel RHS")

    if not lhs or not rhs:
        raise ValueError("LHS o RHS vuoti")
    return name, lhs, rhs
