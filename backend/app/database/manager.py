import os

# Cartella dove salviamo lo stato
STATE_DIR = os.path.join(os.path.dirname(__file__), ".state")
os.makedirs(STATE_DIR, exist_ok=True)

ACTIVE_DB_FILE = os.path.join(STATE_DIR, "active_db.txt")

def list_databases():
    """
    Ricava la lista dei database leggendo il cluster Neo4j tramite cypher.
    NOTA: qui NON importiamo neo4j per evitare circular import.
    L'import verrà fatto localmente dentro la funzione.
    """

    try:
        # import locale → evita circular import
        from .neo4j import get_session

        with get_session("system") as s:
            rows = s.run("SHOW DATABASES").data()

        return [
            row["name"] 
            for row in rows 
            if row.get("currentStatus") == "online"
        ]

    except Exception as e:
        print("WARNING: impossibile leggere i database da Neo4j:", e)
        return ["neo4j"]


def set_active_db(name: str):
    name = name.strip()

    available = list_databases()
    if name not in available:
        raise ValueError(
            f"Database '{name}' non presente. Disponibili: {available}"
        )

    with open(ACTIVE_DB_FILE, "w", encoding="utf-8") as f:
        f.write(name)


def get_current_database_or_default():
    if not os.path.exists(ACTIVE_DB_FILE):
        set_active_db("neo4j")
        return "neo4j"

    with open(ACTIVE_DB_FILE, "r", encoding="utf-8") as f:
        db = f.read().strip()

    if db not in list_databases():
        set_active_db("neo4j")
        return "neo4j"

    return db
