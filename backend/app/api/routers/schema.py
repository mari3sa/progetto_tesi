from fastapi import APIRouter, Depends, HTTPException
from ...config import get_settings
from ...database.neo4j import get_session

router = APIRouter(prefix="/api/schema", tags=["schema"])

@router.get("")
def get_schema(settings = Depends(get_settings)):
    try:
        with get_session(settings.NEO4J_DB) as s:
            # labels
            labels = [r["label"] for r in s.run("""
                MATCH (n) UNWIND labels(n) AS label
                RETURN DISTINCT label ORDER BY label
            """)]
            # relationship types
            rel_types = [r["type"] for r in s.run("""
                CALL db.relationshipTypes() YIELD relationshipType AS type
                RETURN type ORDER BY type
            """)]
            # proprietà per label (opzionale ma utile in futuro)
            props_by_label = {}
            for l in labels:
                keys = [r["k"] for r in s.run(f"""
                    MATCH (n:`{l}`)
                    WITH DISTINCT keys(n) AS ks
                    UNWIND ks AS k
                    RETURN DISTINCT k
                    ORDER BY k
                """)]
                props_by_label[l] = keys
            return {"labels": labels, "rel_types": rel_types, "props_by_label": props_by_label}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")
