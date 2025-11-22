# app/api/routers/measures.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...services.measures import compute_measures

router = APIRouter(prefix="/api/measures", tags=["measures"])

class MeasuresRequest(BaseModel):
    constraints: list[str]

@router.post("/compute")
def measures_compute(req: MeasuresRequest):
    try:
        return compute_measures(req.constraints)
    except ValueError as e:
        # errori di parse RPC o validazione simboli
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
