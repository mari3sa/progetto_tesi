"""
Endpoint dedicati all’ispezione dello schema del database Neo4j.

Il modulo espone un’operazione che restituisce:
- l’elenco delle labels presenti nel grafo,
- i tipi di relazione disponibili,
- i nodi con la loro proprietà `name` (o l'id se il nome non è definito).

L’interrogazione viene eseguita direttamente sul database selezionato,
utilizzando le procedure built-in di Neo4j quando disponibili.
"""


from fastapi import APIRouter, HTTPException
from ...database.neo4j import get_session
from ...database.manager import get_current_database_or_default

router = APIRouter(prefix="/api/schema", tags=["schema"])

#Ritorna labels, relazioni e nodi (property name).
@router.get("")
def get_schema(db: str = None):
    try:
        # Se non viene passato un DB esplicito, usa quello attivo.
        if db is None:
            db = get_current_database_or_default()

        # Apertura sessione Neo4j.
        with get_session(db) as session:

            # Estrae tutte le labels definite nel grafo.
            labels = [
                r["label"] for r in session.run(
                    "CALL db.labels() YIELD label RETURN label"
                )
            ]

            # Estrae tutti i tipi di relazione presenti.
            rel_types = [
                r["type"] for r in session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType AS type RETURN type"
                )
            ]

            # Estrae i nodi usando `name` come etichetta quando possibile.
            nodes = [
                (r["name"] if r["name"] else str(r["id"]))
                for r in session.run("""
                    MATCH (n)
                    RETURN id(n) AS id, n.name AS name
                """)
            ]

        return {
            "labels": labels,
            "rel_types": rel_types,
            "nodes": nodes
        }

    except Exception as e:
        raise HTTPException(500, f"Errore Neo4j: {e}")
