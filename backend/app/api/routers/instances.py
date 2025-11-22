from fastapi import APIRouter, HTTPException
from ...database.manager import (
    list_databases,
    set_active_db,
    get_current_database_or_default,
)

router = APIRouter(prefix="/api/instances", tags=["instances"])


@router.get("")
def get_instances():
    """Ritorna elenco database in formato corretto per il frontend."""
    dbs = list_databases()

    # Conversione da ["neo4j","esempio"] a [{id:"neo4j"}, {id:"esempio"}]
    return {
        "instances": [
            {"id": name, "bolt": "bolt://localhost:7687"}
            for name in dbs
        ]
    }


@router.post("/select/{db_name}")
def select_instance(db_name: str):
    available = list_databases()

    if db_name not in available:
        raise HTTPException(404, f"Database '{db_name}' non trovato")

    set_active_db(db_name)
    return {"selected": db_name}


@router.get("/current")
def current_instance():
    return {"current": get_current_database_or_default()}
