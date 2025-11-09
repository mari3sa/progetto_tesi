# app/db/neo4j.py
from neo4j import GraphDatabase, Session
from typing import Optional
from .manager import get_active_profile

_driver = None  # driver Neo4j globale (riusato)

def init_driver(uri: str, user: str, password: str) -> None:
    """Inizializza (o re-inizializza) il driver globale."""
    global _driver
    if _driver is not None:
        _driver.close()
    _driver = GraphDatabase.driver(uri, auth=(user, password))

def init_driver_from_active_profile() -> None:
    """Inizializza il driver usando il profilo attivo (da manager)."""
    prof = get_active_profile()
    init_driver(prof["uri"], prof["user"], prof["password"])

def get_session(database: str) -> Session:
    """Ritorna una sessione sul database richiesto.
    Se il driver non è inizializzato, usa il profilo attivo per inizializzarlo.
    """
    global _driver
    if _driver is None:
        init_driver_from_active_profile()
    return _driver.session(database=database)

def close_driver() -> None:
    """Chiude il driver globale."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
