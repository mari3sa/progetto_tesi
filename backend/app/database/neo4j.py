"""
Utility per la gestione del driver Neo4j e delle sessioni verso il database.

Il modulo espone funzioni per inizializzare il driver, aprire una sessione
verso il database attivo e chiudere eventuali connessioni. Le credenziali
vengono lette dalla configurazione dell’applicazione e ogni sessione è
collegata automaticamente al database selezionato tramite lo stato interno.
"""

from neo4j import GraphDatabase
from .manager import get_current_database_or_default

_driver = None

#Inizializza il driver globale se non è già stato creato.
def init_driver(uri: str, user: str, password: str):
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(uri, auth=(user, password))

#Crea un driver per l'istanza corrente.
#Usa sempre le credenziali del profilo .env.
def get_driver():
    from ..config import get_settings
    settings = get_settings()
    return GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

#Restituisce una sessione collegata al database attivo.
#Se il nome non è specificato, viene usato quello salvato nello stato.
def get_session(database: str = None):
    if database is None:
        database = get_current_database_or_default()

    driver = get_driver()
    return driver.session(database=database)

#Chiude il driver globale, se presente, e lo resetta.
def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
