from neo4j import GraphDatabase, Session
from typing import Optional

_driver = None 

def init_driver(uri: str, user: str, password: str):
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(uri, auth=(user, password))

def get_session(database: str) -> Session:
    if _driver is None:
        raise RuntimeError("Neo4j driver non inizializzato")
    return _driver.session(database=database)

def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
