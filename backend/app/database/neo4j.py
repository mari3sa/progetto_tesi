from neo4j import GraphDatabase
from .manager import get_current_database_or_default

# Driver globale
_driver = None

def init_driver(uri: str, user: str, password: str):
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(uri, auth=(user, password))

def get_driver():
    """
    Crea un driver per l'istanza corrente.
    Usa sempre le credenziali del profilo .env.
    """
    from ..config import get_settings
    settings = get_settings()
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

def get_session(database: str = None):
    """
    Ritorna una sessione collegata al database attivo.
    """
    if database is None:
        database = get_current_database_or_default()

    driver = get_driver()
    return driver.session(database=database)

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
