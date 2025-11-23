"""
Funzioni di gestione dello stato del database attivo e di lettura dei database
disponibili in un cluster Neo4j.

Il modulo mantiene un piccolo file locale che memorizza quale database è
attualmente selezionato.  
Espone tre funzioni principali:

- list_databases(): interroga Neo4j e restituisce i database online.
- set_active_db(): salva il nome del database attivo.
- get_current_database_or_default(): legge lo stato salvato e applica un
  fallback automatico a 'neo4j' se necessario.

L'import del driver Neo4j è eseguito localmente nelle funzioni per evitare
cicli di importazione.
"""

import os

# Cartella dove salviamo lo stato
STATE_DIR = os.path.join(os.path.dirname(__file__), ".state")
os.makedirs(STATE_DIR, exist_ok=True)

# File che contiene il nome del database attivo.
ACTIVE_DB_FILE = os.path.join(STATE_DIR, "active_db.txt")


#Ricava la lista dei database leggendo il cluster Neo4j tramite cypher.
def list_databases():
    """
    NOTA: qui NON importiamo neo4j per evitare circular import.
    L'import verrà fatto localmente dentro la funzione.
    """

    try:
        # Import locale per evitare dipendenze circolari.
        from .neo4j import get_session

        # Usiamo il database 'system' per la query SHOW DATABASES.
        with get_session("system") as s:
            rows = s.run("SHOW DATABASES").data()

        # Ritorniamo solo quelli online.
        return [
            row["name"] 
            for row in rows 
            if row.get("currentStatus") == "online"
        ]

    except Exception as e:
        print("WARNING: impossibile leggere i database da Neo4j:", e)
        return ["neo4j"]

#Imposta e salva localmente il database attualmente selezionato.
def set_active_db(name: str):
    name = name.strip()

    available = list_databases()
    if name not in available:
        raise ValueError(
            f"Database '{name}' non presente. Disponibili: {available}"
        )

    # Scrive il database selezionato nel file di stato.
    with open(ACTIVE_DB_FILE, "w", encoding="utf-8") as f:
        f.write(name)

# Restituisce il database attualmente salvato nello stato.
#Se il file non esiste o contiene un nome non valido,
#viene impostato e ritornato il database 'neo4j'
def get_current_database_or_default():
    if not os.path.exists(ACTIVE_DB_FILE):
        set_active_db("neo4j")
        return "neo4j"

    with open(ACTIVE_DB_FILE, "r", encoding="utf-8") as f:
        db = f.read().strip()

    # Se il database salvato non è più disponibile, fallback su 'neo4j'.
    if db not in list_databases():
        set_active_db("neo4j")
        return "neo4j"

    return db
