from typing import List, Dict, Any
from ..database.neo4j import get_session
from ..config import get_settings
from ..domain.models import Constraint, NodeLabelConstraint, EdgeTypeConstraint
from ..database.manager import get_current_database_or_default


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

def validate_constraints(constraints: List[Constraint]) -> dict:
    labels, rel_types = load_schema_from_db()
    errors: List[Dict[str, Any]] = []

    for i, c in enumerate(constraints):
        if isinstance(c, NodeLabelConstraint):
            if c.label not in labels:
                errors.append({"index": i, "field": "label",
                               "message": f"Label '{c.label}' non presente nel grafo"})
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
