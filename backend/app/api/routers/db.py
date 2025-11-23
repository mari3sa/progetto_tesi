"""
Endpoint dedicati alla gestione dei database disponibili nell'applicazione.

Questo modulo espone operazioni per:
- ottenere l'elenco dei database configurati,
- selezionare quale utilizzare come database attivo,
- recuperare il database attualmente selezionato.

La logica vera e propria (lettura della lista, selezione e stato corrente)
è delegata al livello `database.manager`; qui viene gestita l'esposizione
tramite API e la validazione degli input.
"""

from fastapi import APIRouter, HTTPException
from ...database.manager import list_databases, set_active_db, get_current_database_or_default

router = APIRouter(prefix="/api/db", tags=["database"])

# Restituisce l'elenco dei database disponibili e quello attualmente attivo.
@router.get("/databases")
def get_databases():
    try:
        return {
            "databases": list_databases(),
            "current": get_current_database_or_default()
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# Imposta come attivo uno dei database configurati.
@router.post("/select")
def select_database(name: str):
    available = list_databases()

    if name not in available:
        raise HTTPException(404, f"Database '{name}' non trovato")

    set_active_db(name)
    return {"selected": name}

# Restituisce il nome del database attualmente in uso.
@router.get("/current")
def current_database():
    return {"current": get_current_database_or_default()}
