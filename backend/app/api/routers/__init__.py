"""
Raccolta dei router utilizzati dall’applicazione.

Questo modulo importa e re-esporta i vari router che gestiscono le diverse
sezioni dell’API, mantenendo ordinata la struttura del progetto e offrendo
un punto di aggregazione unico per l’applicazione principale.

Router inclusi:
- test_router: endpoint di test e diagnostica.
- graph_router: operazioni per la gestione e manipolazione dei grafi.
- schema_router: servizi per la definizione e la validazione degli schemi.
- constraints_router: logica relativa ai vincoli applicati ai dati o ai grafi.
- rpq_router: gestione delle Regular Path Queries.
- db_router: funzionalità di accesso al database.
- measures_router: calcolo e gestione delle misure di inconsistenza.
- instances_router: operazioni sulle istanze dei modelli o dei dati.
"""

from .test import router as test_router
from .graph import router as graph_router
from .schema import router as schema_router
from .constraints import router as constraints_router
from .rpq import router as rpq_router
from .db import router as db_router
from .measures import router as measures_router
from .instances import router as instances_router