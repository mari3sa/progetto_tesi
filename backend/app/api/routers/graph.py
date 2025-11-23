"""
Endpoint dedicati all’esplorazione del grafo archiviato nel database Neo4j.

Il modulo fornisce funzioni per:
- generare un’immagine del grafo (nodi + relazioni),
- recuperare l’elenco dei nodi presenti.

Il grafo viene ricostruito dinamicamente interrogando il database selezionato.
Il disegno dell’immagine utilizza NetworkX e Matplotlib.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from ...database.manager import set_active_db, get_current_database_or_default
from ...database.neo4j import get_session

import io
import networkx as nx
import matplotlib

matplotlib.use("Agg")  # backend sicuro per server/headless
import matplotlib.pyplot as plt

# Endpoint per la generazione e consultazione del grafo.
router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/image")
def get_graph_image(instance: str = Query(...)):

    # 1) Seleziona database
    try:
        set_active_db(instance)
    except Exception:
        raise HTTPException(400, f"Database '{instance}' non esiste.")

    db = get_current_database_or_default()

    # 2) Estrae nodi + relazioni
    try:
        with get_session(db) as s:

            # id + nome nodo
            node_rows = list(
                s.run("""
                    MATCH (n)
                    RETURN id(n) AS id, n.name AS name
                """)
            )

            nodes = [r["id"] for r in node_rows]

            # Mappa: id → etichetta da visualizzare.
            labels_map = {
                r["id"]: (r["name"] if r["name"] else str(r["id"]))
                for r in node_rows
            }

            # Lettura relazioni con tipo e nodi estremi.
            edges = [
                (r["a"], r["b"], r["type"])
                for r in s.run("""
                    MATCH (a)-[r]->(b)
                    RETURN id(a) AS a, id(b) AS b, type(r) AS type
                """)
            ]

    except Exception as e:
        raise HTTPException(500, f"Errore Neo4j: {e}")

    if not nodes:
        raise HTTPException(400, "Il grafo è vuoto, impossibile generare immagine.")

    # 3) Costruzione grafo
    G = nx.DiGraph()
    G.add_nodes_from(nodes)

    for a, b, t in edges:
        G.add_edge(a, b, label=t)

    # 4) Disegno immagine
    try:
        fig = plt.figure(figsize=(6, 5))
        pos = nx.spring_layout(G)

        nx.draw(
            G,
            pos,
            labels=labels_map,
            with_labels=True,
            node_size=600,
            font_size=8,
            arrows=True
        )

        edge_labels = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)

    except Exception as e:
        raise HTTPException(500, f"Errore generazione immagine: {e}")

    return StreamingResponse(buf, media_type="image/png")


 
#Restituisce la lista dei nodi del grafo corrente (proprietà name).
@router.get("/nodes")
def get_graph_nodes(instance: str = Query(...)):
   
    try:
        set_active_db(instance)
    except Exception:
        raise HTTPException(400, f"Database '{instance}' non esiste.")

    db = get_current_database_or_default()

    # Recupero nodi dal database Neo4j.
    try:
        with get_session(db) as s:
            node_rows = list(
                s.run("""
                    MATCH (n)
                    RETURN id(n) AS id, n.name AS name
                """)
            )
    except Exception as e:
        raise HTTPException(500, f"Errore Neo4j: {e}")

    # Conversione in lista leggibile (nome o id).
    nodes = [
        (r["name"] if r["name"] else str(r["id"]))
        for r in node_rows
    ]

    return {"nodes": nodes}
