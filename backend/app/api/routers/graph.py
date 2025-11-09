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

@router.get("/nodes")
def list_nodes(settings = Depends(get_settings)):
    """
    Return nodes with their id, labels, and properties
    """
    try:
        with get_session(settings.NEO4J_DB) as s:
            result = s.run("""
            MATCH (n)
            RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props
            LIMIT 200
        """)
        nodes = [r.data() for r in result]
        return {"nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")

@router.get("/relationships")
def list_relationships(settings = Depends(get_settings)):
    try:
        with get_session(settings.NEO4J_DB) as session:
            result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN id(a) AS start, type(r) AS type, id(b) AS end, properties(r) AS props
            LIMIT 200
        """)
        rels = [r.data() for r in result]
        return {"relationships": rels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")
