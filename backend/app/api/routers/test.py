from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["test"])

@router.get("/hello")
def hello():
    return {"message": "Ciao dal backend FastAPI!"}
