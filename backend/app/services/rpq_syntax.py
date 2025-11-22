# app/services/rpq_syntax.py

from typing import List, Tuple

# Ogni simbolo atomico è una coppia (inv, label)
# inv: bool (False = direzione normale, True = inversa)
# label: str (es. "child_of")
Atom = Tuple[bool, str]


# ===========================
# TOKENIZER
# ===========================

Token = Tuple[str, str]  # (kind, value)


def _tokenize(expr: str) -> List[Token]:
    """
    Trasforma una stringa RPQ in una lista di token.
    Supporta:
      - parentesi: ( )
      - OR: |  (anche '∣' che viene normalizzato a '|')
      - concatenazione: '.' o implicita per adiacenza
      - identificatori: child_of, grandson_of, ecc.
      - ignora eventuale ';' finale
    """
    expr = expr.strip()
    tokens: List[Token] = []
    i = 0
    n = len(expr)

    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        if ch == ';':
            # ignora tutto ciò che viene dopo il ';'
            break

        if ch == '(':
            tokens.append(("LPAREN", ch))
            i += 1
            continue

        if ch == ')':
            tokens.append(("RPAREN", ch))
            i += 1
            continue

        if ch == '|' or ch == '∣':
            tokens.append(("OR", "|"))
            i += 1
            continue

        if ch == '.':
            tokens.append(("DOT", "."))
            i += 1
            continue

        # identificatore (relazione) – lettere, cifre, underscore
        if ch.isalpha() or ch == '_':
            start = i
            i += 1
            while i < n and (expr[i].isalnum() or expr[i] == '_'):
                i += 1
            ident = expr[start:i]
            tokens.append(("IDENT", ident))
            continue

        # qualunque altro carattere non riconosciuto → errore
        raise ValueError(f"Carattere non valido nella RPQ: '{ch}'")

    tokens.append(("EOF", ""))  # sentinella
    return tokens


# ===========================
# PARSER RPQ
# ===========================

class _RPQParser:
    """
    Parser ricorsivo per un'espressione RPQ.

    Ritorna una lista di alternative:
        List[List[Atom]]

    dove ogni alternativa è una sequenza di (inv, label).
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, kind: str) -> Token:
        tok = self._peek()
        if tok[0] != kind:
            raise ValueError(f"Atteso token {kind} ma trovato {tok[0]}")
        return self._advance()

    # RPQ := ALT
    def parse_rpq(self) -> List[List[Atom]]:
        alts = self._parse_alt()
        # alla fine dobbiamo essere a EOF (o RPAREN consumata da chi ci chiama)
        if self._peek()[0] not in ("EOF", "RPAREN"):
            kind, val = self._peek()
            raise ValueError(f"Token inatteso '{val}' ({kind}) alla fine della RPQ")
        return alts

    # ALT := CONCAT ( 'OR' CONCAT )*
    def _parse_alt(self) -> List[List[Atom]]:
        alts = self._parse_concat()
        while self._peek()[0] == "OR":
            self._advance()
            right = self._parse_concat()
            alts.extend(right)
        return alts

    # CONCAT := FACTOR ( (DOT)? FACTOR )*
    # concatenazione esplicita con '.' o implicita per adiacenza
    def _parse_concat(self) -> List[List[Atom]]:
        alts = self._parse_factor()

        while True:
            kind, _ = self._peek()

            if kind == "DOT":
                # concatenazione esplicita
                self._advance()
                rhs = self._parse_factor()
                alts = self._concat_alts(alts, rhs)
            elif kind in ("IDENT", "LPAREN"):
                # concatenazione implicita
                rhs = self._parse_factor()
                alts = self._concat_alts(alts, rhs)
            else:
                break

        return alts

    # FACTOR := IDENT | '(' ALT ')'
    def _parse_factor(self) -> List[List[Atom]]:
        kind, val = self._peek()

        if kind == "IDENT":
            self._advance()
            # eventuale supporto rel^-1 in futuro; per ora inv = False
            inv = False
            label = val
            return [[(inv, label)]]

        if kind == "LPAREN":
            self._advance()
            inner = self._parse_alt()
            self._expect("RPAREN")
            return inner

        raise ValueError(f"Token inatteso '{val}' ({kind}) in fattore RPQ")

    @staticmethod
    def _concat_alts(
        left: List[List[Atom]],
        right: List[List[Atom]]
    ) -> List[List[Atom]]:
        if not left:
            return right
        if not right:
            return left
        out: List[List[Atom]] = []
        for a in left:
            for b in right:
                out.append(a + b)
        return out


def parse_rpq(expr: str) -> List[List[Atom]]:
    """
    Parsea una sola RPQ (senza nome, solo parte sinistra o destra di un vincolo).
    Ritorna: lista di alternative, ciascuna è una lista di (inv, label).

    Esempi accettati:
      - child_of
      - child_of.child_of
      - child_of (brother_of|sister_of)
      - (child_of.child_of)|(son_of.daughter_of)
    """
    expr = expr.strip()
    # normalizza OR unicode
    expr = expr.replace("∣", "|")
    tokens = _tokenize(expr)
    parser = _RPQParser(tokens)
    return parser.parse_rpq()


# ===========================
# PARSER DI UN VINCOLO RPC
# ===========================

def parse_rpc(constraint_str: str) -> Tuple[str, List[List[Atom]], List[List[Atom]]]:
    """
    Parsea un vincolo RPC del tipo:

        C1 = child_of ⊆ son_of|daughter_of
        C_2: child_of.(brother_of|sister_of) ⊆ nephew_of|niece_of;
        C_3 = child_of.child_of <= grandson_of|granddaughter_of

    Ritorna:
        (name, lhs_alternatives, rhs_alternatives)

    dove lhs_alternatives / rhs_alternatives sono liste di sequenze:
        List[List[(inv: bool, label: str)]]
    """
    s = constraint_str.strip()

    if not s:
        raise ValueError("Vincolo vuoto")

    # togli eventuale ';' finale grossolano
    if s.endswith(";"):
        s = s[:-1].strip()

    # normalizza simbolo di inclusione
    s = s.replace("<=", "⊆")  # supporta anche '<=' come in molti esempi

    # separa nome e resto: cerchiamo '=' oppure ':'
    eq_pos = s.find("=")
    colon_pos = s.find(":")

    if eq_pos == -1 and colon_pos == -1:
        raise ValueError("Manca '=' o ':' nel vincolo RPC")

    if eq_pos != -1 and (colon_pos == -1 or eq_pos < colon_pos):
        name_end = eq_pos
    else:
        name_end = colon_pos

    name = s[:name_end].strip()
    body = s[name_end + 1 :].strip()

    if not name:
        raise ValueError("Nome del vincolo mancante (es. 'C1', 'C_2', ecc.)")

    # split su '⊆'
    parts = body.split("⊆")
    if len(parts) != 2:
        raise ValueError("Il vincolo deve contenere esattamente un simbolo '⊆' o '<='")

    lhs_str = parts[0].strip()
    rhs_str = parts[1].strip()

    # togli eventuale ';' finale su RHS
    if rhs_str.endswith(";"):
        rhs_str = rhs_str[:-1].strip()

    if not lhs_str or not rhs_str:
        raise ValueError("Parte sinistra o destra vuota nel vincolo RPC")

    lhs_alts = parse_rpq(lhs_str)
    rhs_alts = parse_rpq(rhs_str)

    return name, lhs_alts, rhs_alts
