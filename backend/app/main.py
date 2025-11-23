"""
Configurazione e inizializzazione dell’app FastAPI.

Il modulo definisce:
- la gestione del ciclo di vita dell’app (apertura/chiusura driver Neo4j),
- la configurazione del middleware CORS,
- il montaggio di tutti i router dell’API.

L’avvio del driver avviene nella fase di startup tramite il context manager
`lifespan`, mentre in fase di shutdown viene effettuata la chiusura pulita
della connessione.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .api.routers import test_router, graph_router,schema_router,constraints_router, rpq_router, db_router, measures_router, instances_router


from .database.neo4j import init_driver, close_driver

# Gestione del ciclo di vita dell’app:
# inizializza il driver alla startup, lo chiude allo shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    init_driver(s.NEO4J_URI, s.NEO4J_USER, s.NEO4J_PASSWORD)
    try:
        yield
    finally:
        close_driver()

# Creazione dell’applicazione FastAPI con lifecycle personalizzato.
app = FastAPI(lifespan=lifespan)

# Configurazione CORS permettendo al frontend di accedere all’API.
#CORS significa Cross-Origin Resource Sharing.
#È un meccanismo di sicurezza dei browser che decide quali siti 
#web possono fare richieste a un certo server.
s = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrazione dei router dell’API.
app.include_router(test_router)
app.include_router(graph_router)
app.include_router(schema_router)
app.include_router(constraints_router)
app.include_router(rpq_router)
app.include_router(db_router)
app.include_router(measures_router)
app.include_router(instances_router)

