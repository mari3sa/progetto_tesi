"""
Endpoint dedicati al calcolo delle misure basate sui vincoli.

Il modulo espone un’unica operazione che riceve un elenco di vincoli e
delegando la logica di calcolo al servizio `compute_measures`.  
Gestisce eventuali errori di validazione o parsing restituendo risposte
coerenti con l’API.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...services.measures import compute_measures

router = APIRouter(prefix="/api/measures", tags=["measures"])

# Modello di richiesta che contiene l'elenco dei vincoli.
class MeasuresRequest(BaseModel):
    constraints: list[str]

#Calcola le misure associate ai vincoli forniti.
@router.post("/compute")
def measures_compute(req: MeasuresRequest):
    # Delegazione completa della logica di calcolo al servizio.
    try:
        return compute_measures(req.constraints)
    except ValueError as e:
        # Errori legati alla sintassi dei vincoli o a simboli non validi.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Qualsiasi altro errore interno non previsto.
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
