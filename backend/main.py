from typing import Union
from neo4j import GraphDatabase
from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB = os.getenv("NEO4J_DB", "neo4j")

app = FastAPI()

# Connessione al database
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


from fastapi import HTTPException

#Metodo per testare la connessione al database Neo4j
@app.get("/api/neo4j/ping")
def neo4j_ping():
    try:
        with driver.session(database=NEO4J_DB) as session:
            rec = session.run("RETURN 1 AS ok").single()
            return {"ok": rec["ok"] == 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")
