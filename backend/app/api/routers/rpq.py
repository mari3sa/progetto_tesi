from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...services.rpq_inclusion import check_inclusion

router = APIRouter(prefix="/api/rpq", tags=["rpq"])

class RPQConstraint(BaseModel):
    constraint: str  # es: "C_3=child_of.child_of⊆grandson_of∣granddaughter_of"

@router.post("/check")
def rpq_check(payload: RPQConstraint):
    try:
        return check_inclusion(payload.constraint)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore: {e}")
