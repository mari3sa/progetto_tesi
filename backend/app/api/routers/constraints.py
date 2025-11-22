from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime
from pathlib import Path
import json

from ...domain.models import ConstraintsPayload
from ...services.constraints_service import validate_constraints

router = APIRouter(prefix="/api/constraints", tags=["constraints"])

DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "constraints"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _save_constraints(payload: dict) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = DATA_DIR / f"constraints-{ts}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return fname.name

@router.post("/validate")
def validate(payload: ConstraintsPayload):
    result = validate_constraints(payload.constraints)
    return result

@router.post("/save")
def save_constraints(payload: ConstraintsPayload):
    result = validate_constraints(payload.constraints)
    if not result["ok"]:
        return {"ok": False, "errors": result["errors"]}
    fname = _save_constraints(payload.model_dump())
    return {"ok": True, "file": fname}

@router.get("/files")
def list_files():
    files = sorted([p.name for p in DATA_DIR.glob("constraints-*.json")])
    return {"files": files}

@router.get("/file/{name}")
def get_file(name: str):
    fp = DATA_DIR / name
    if not fp.exists():
        raise HTTPException(404, "File non trovato")
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@router.post("/import")
def import_constraints(file: UploadFile = File(...)):
    try:
        raw = file.file.read()
        payload = json.loads(raw)
    finally:
        file.file.close()

    if "constraints" not in payload or not isinstance(payload["constraints"], list):
        raise HTTPException(400, "Formato non valido: atteso { constraints: [...] }")

    result = validate_constraints(payload["constraints"])

    # RITORNO COMPATIBILE CON IL FRONTEND
    return {
        "constraints": payload["constraints"],
        "ok": result["ok"],
        "errors": result["errors"]
    }

