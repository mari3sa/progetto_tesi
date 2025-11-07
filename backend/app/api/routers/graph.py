from fastapi import APIRouter, Depends, HTTPException
from ...config import get_settings
from ...database.neo4j import get_session

router = APIRouter(prefix="/api", tags=["graph"])

@router.get("/neo4j/ping")
def neo4j_ping(settings = Depends(get_settings)):
    try:
        with get_session(settings.NEO4J_DB) as s:
            ok = s.run("RETURN 1 AS ok").single()["ok"]
            return {"ok": ok == 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")

@router.get("/graph/stats")
def graph_stats(settings = Depends(get_settings)):
    try:
        with get_session(settings.NEO4J_DB) as s:
            nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels  = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            return {"nodes": nodes, "relationships": rels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")
