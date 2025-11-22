from fastapi import APIRouter, HTTPException
from ...database.neo4j import get_session
from ...database.manager import get_current_database_or_default

router = APIRouter(prefix="/api/schema", tags=["schema"])


@router.get("")
def get_schema(db: str = None):
    """Ritorna labels, relazioni e nodi (property name)."""

    try:
        if db is None:
            db = get_current_database_or_default()

        with get_session(db) as session:

            labels = [
                r["label"] for r in session.run(
                    "CALL db.labels() YIELD label RETURN label"
                )
            ]

            rel_types = [
                r["type"] for r in session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type"
                )
            ]

            # 🆕 estrai nomi dei nodi
            nodes = [
                (r["name"] if r["name"] else str(r["id"]))
                for r in session.run("""
                    MATCH (n)
                    RETURN id(n) AS id, n.name AS name
                """)
            ]

        return {
            "labels": labels,
            "rel_types": rel_types,
            "nodes": nodes
        }

    except Exception as e:
        raise HTTPException(500, f"Errore Neo4j: {e}")
