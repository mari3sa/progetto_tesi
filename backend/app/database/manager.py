# app/db/conn_manager.py

from typing import Optional
import os

# ✅ Stato interno
_active_profile: Optional[dict] = None
_active_db: Optional[str] = None

def load_default_profile() -> dict:
    """Preleva credenziali da .env oppure variabili ambiente"""
    return {
        "uri": os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password"),
        "database": os.getenv("NEO4J_DB", "neo4j"),
    }

def set_active_profile(profile: dict):
    """Imposta il profilo attivo (URI + credenziali)"""
    global _active_profile
    _active_profile = profile

def get_active_profile() -> dict:
    """Ritorna il profilo attivo, se non c’è crea quello di default"""
    global _active_profile
    if _active_profile is None:
        _active_profile = load_default_profile()
    return _active_profile


# ✅ DB selezionato (dentro il profilo)
def set_active_db(name: str | None):
    global _active_db
    _active_db = name

def get_active_db() -> Optional[str]:
    return _active_db

def get_current_database_or_default() -> str:
    """Se l’utente non ha scelto nulla → usa database predefinito"""
    prof = get_active_profile()
    return _active_db or prof["database"]
