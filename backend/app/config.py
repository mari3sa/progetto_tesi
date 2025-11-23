"""
Definizione delle impostazioni dell’applicazione e caricamento centralizzato
delle variabili di configurazione.

Le impostazioni sono gestite tramite Pydantic Settings, con supporto al
caricamento automatico da file .env. Il modulo espone una funzione
`get_settings()` con cache interna, così da evitare ricostruzioni ripetute.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Modello delle impostazioni dell’applicazione:
# - origin consentite
# - parametri di connessione a Neo4j
# - percorso file .env
class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = ["http://localhost:5173","http://127.0.0.1:5173"]
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DB: str = "neo4j"
    # Configurazione di Pydantic Settings: carica variabili da .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
@lru_cache
def get_settings() -> Settings:
    return Settings()
