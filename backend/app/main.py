from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .api.routers import test_router, graph_router,schema_router,constraints_router, rpq_router, db_router, measures_router, instances_router


from .database.neo4j import init_driver, close_driver



@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    init_driver(s.NEO4J_URI, s.NEO4J_USER, s.NEO4J_PASSWORD)
    try:
        yield
    finally:
        close_driver()

app = FastAPI(lifespan=lifespan)

s = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=s.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_router)
app.include_router(graph_router)
app.include_router(schema_router)
app.include_router(constraints_router)
app.include_router(rpq_router)
app.include_router(db_router)
app.include_router(measures_router)
app.include_router(instances_router)

