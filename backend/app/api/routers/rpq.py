"""
Endpoint dedicati alla verifica di inclusione tra RPQ (Regular Path Queries).

Questo modulo espone un’operazione per controllare se un vincolo RPQ
rispetta la relazione di inclusione specificata.  
La logica di calcolo è delegata al servizio `check_inclusion`, mentre qui
vengono gestiti input, validazione e formattazione degli errori.
"""


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...services.rpq_inclusion import check_inclusion

router = APIRouter(prefix="/api/rpq", tags=["rpq"])

# Modello che rappresenta un singolo vincolo RPQ da verificare.
class RPQConstraint(BaseModel):
    constraint: str  # es: "C_3=child_of.child_of⊆grandson_of∣granddaughter_of"

#Verifica la relazione di inclusione definita nel vincolo RPQ.v
@router.post("/check")
def rpq_check(payload: RPQConstraint):
    try:
        # Delegazione al servizio che esegue la logica di calcolo.
        return check_inclusion(payload.constraint)
    except ValueError as e:
        # Errori tipicamente dovuti a sintassi RPQ non valida.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Errori imprevisti lato server.
        raise HTTPException(status_code=500, detail=f"Errore: {e}")
