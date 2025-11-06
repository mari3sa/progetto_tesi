from typing import Union
from neo4j import GraphDatabase
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB = os.getenv("NEO4J_DB", "neo4j")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@app.get("/api/hello")
def hello():
    return {"message": "Ciao dal backend FastAPI!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/api/neo4j/ping")
def neo4j_ping():
    try:
        with driver.session(database=NEO4J_DB) as session:
            rec = session.run("RETURN 1 AS ok").single()
            return {"ok": rec["ok"] == 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j error: {e}")
