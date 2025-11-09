from fastapi import APIRouter, HTTPException
from ...database.neo4j import get_session
from ...database.manager import get_active_profile, set_active_db, get_current_database_or_default

router = APIRouter(prefix="/api/db", tags=["database"])

@router.get("/databases")
def list_databases():
    """Elenca i database disponibili (richiede permesso su 'system')."""
    prof = get_active_profile()
    if not prof:
        raise HTTPException(400, "No active profile")
    try:
        with get_session("system") as s:  # Neo4j 5: SHOW DATABASES gira su 'system'
            rows = s.run("SHOW DATABASES").data()
            # solo quelli ONLINE
            names = [r["name"] for r in rows if r.get("currentStatus","") == "online"]
            return {"databases": names, "default": prof["database"]}
    except Exception as e:
        raise HTTPException(500, f"Neo4j error: {e}")

@router.post("/select")
def select_database(name: str):
    """Imposta il database 'attivo' per le richieste successive."""
    # opzionale: verifica che esista
    try:
        with get_session("system") as s:
            rows = s.run("SHOW DATABASES WHERE name = $n", n=name).data()
            if not rows:
                raise HTTPException(404, f"Database '{name}' not found")
            if rows[0].get("currentStatus","") != "online":
                raise HTTPException(400, f"Database '{name}' is not online")
        set_active_db(name)
        return {"selected": name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Neo4j error: {e}")

@router.get("/current")
def current_database():
    try:
        return {"database": get_current_database_or_default()}
    except Exception as e:
        raise HTTPException(400, str(e))
