"""
Funzioni per il caricamento dello schema dal database e la validazione
dei vincoli definiti dall’utente.

Il modulo interroga Neo4j per ottenere:
- l’elenco delle labels presenti,
- i tipi di relazione disponibili.

Sulla base di queste informazioni controlla che ogni vincolo fornito
sia coerente con lo schema corrente del grafo.
"""

from typing import List, Dict, Any
from ..database.neo4j import get_session
from ..config import get_settings
from ..domain.models import Constraint, NodeLabelConstraint, EdgeTypeConstraint
from ..database.manager import get_current_database_or_default


#Carica dallo schema Neo4j tutte le labels e i tipi di relazione disponibili.
def load_schema_from_db():
    s = get_settings()
    with get_session(get_current_database_or_default()) as session:
        labels = {r["label"] for r in session.run("""
            MATCH (n) UNWIND labels(n) AS label
            RETURN DISTINCT label
        """)}
        rel_types = {r["type"] for r in session.run("""
            CALL db.relationshipTypes() YIELD relationshipType AS type
            RETURN type
        """)}
    return labels, rel_types

    """
    Valida la lista di vincoli confrontandoli con lo schema corrente.
    Controlla che labels e relazioni indicate nei vincoli esistano davvero.

    Ritorna un dizionario con:
    - ok: boolean (True se nessun errore),
    - errors: elenco dettagliato delle violazioni.
    """
def validate_constraints(constraints: List[Constraint]) -> dict:
    labels, rel_types = load_schema_from_db()
    errors: List[Dict[str, Any]] = []

    # Verifica ogni vincolo con controllo puntuale.
    for i, c in enumerate(constraints):
        # Vincolo di esistenza label.
        if isinstance(c, NodeLabelConstraint):
            if c.label not in labels:
                errors.append({"index": i, "field": "label",
                               "message": f"Label '{c.label}' non presente nel grafo"})
        # Vincolo di tipo di relazione tra due label.
        elif isinstance(c, EdgeTypeConstraint):
            if c.from_label not in labels:
                errors.append({"index": i, "field": "from_label",
                               "message": f"Label '{c.from_label}' non presente"})
            if c.to_label not in labels:
                errors.append({"index": i, "field": "to_label",
                               "message": f"Label '{c.to_label}' non presente"})
            if c.rel_type not in rel_types:
                errors.append({"index": i, "field": "rel_type",
                               "message": f"RelType '{c.rel_type}' non presente"})
    return {"ok": len(errors) == 0, "errors": errors}
