from fastapi import APIRouter, HTTPException
from ...database.manager import list_databases, set_active_db, get_current_database_or_default

router = APIRouter(prefix="/api/db", tags=["database"])

@router.get("/databases")
def get_databases():
    try:
        return {
            "databases": list_databases(),
            "current": get_current_database_or_default()
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/select")
def select_database(name: str):
    available = list_databases()

    if name not in available:
        raise HTTPException(404, f"Database '{name}' non trovato")

    set_active_db(name)
    return {"selected": name}

@router.get("/current")
def current_database():
    return {"current": get_current_database_or_default()}
