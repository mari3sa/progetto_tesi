"""
Endpoint dedicati alla gestione delle istanze (database) disponibili
nell’applicazione.

Il modulo espone operazioni per:
- restituire l'elenco delle istanze in un formato compatibile con il frontend,
- selezionare l’istanza attiva,
- recuperare l’istanza attualmente in uso.

La logica di accesso e gestione dei database è delegata al livello
`database.manager`.
"""

from fastapi import APIRouter, HTTPException
from ...database.manager import (
    list_databases,
    set_active_db,
    get_current_database_or_default,
)

router = APIRouter(prefix="/api/instances", tags=["instances"])

#Restituisce elenco database in formato corretto per il frontend.
@router.get("")
def get_instances():
    dbs = list_databases()

    # Conversione da ["neo4j","esempio"] a [{id:"neo4j"}, {id:"esempio"}]
    return {
        "instances": [
            {"id": name, "bolt": "bolt://localhost:7687"}
            for name in dbs
        ]
    }


#Imposta come attiva una specifica istanza/database.
@router.post("/select/{db_name}")
def select_instance(db_name: str):
    available = list_databases()

    # Controlla che il database richiesto esista.
    if db_name not in available:
        raise HTTPException(404, f"Database '{db_name}' non trovato")

    # Aggiorna il database attivo.
    set_active_db(db_name)
    return {"selected": db_name}


#Restituisce il nome dell’istanza attualmente selezionata.
@router.get("/current")
def current_instance():
    return {"current": get_current_database_or_default()}
