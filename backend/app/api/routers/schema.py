from fastapi import APIRouter, HTTPException
from ...database.neo4j import get_session
from ...database.manager import get_current_database_or_default

router = APIRouter(prefix="/api/schema", tags=["schema"])

@router.get("")
def get_schema(db: str = None):
    """Ritorna labels e relazioni del grafo."""
    try:
        if db is None:
            db = get_current_database_or_default()

        with get_session(db) as session:
            labels = [r["label"] for r in session.run(
                "CALL db.labels() YIELD label RETURN label"
            )]

            rel_types = [r["type"] for r in session.run(
                "CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type"
            )]

        return {"labels": labels, "rel_types": rel_types}

    except Exception as e:
        raise HTTPException(500, f"Errore Neo4j: {e}")
