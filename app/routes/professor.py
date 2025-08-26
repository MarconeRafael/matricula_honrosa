from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import json
from uuid import uuid4
from datetime import datetime

from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/professor", tags=["professor"])

templates = Jinja2Templates(directory="app/templates")

DATA_REQ_FILE = Path("data/association_requests.json")
DATA_REQ_FILE.parent.mkdir(parents=True, exist_ok=True)
if not DATA_REQ_FILE.exists():
    DATA_REQ_FILE.write_text("[]")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ROTA HTML ----------
@router.get("/solicitacoes", response_class=HTMLResponse)
def view_requests(request: Request):
    """
    Renderiza a tela de solicitações de associação de turmas.
    """
    return templates.TemplateResponse("solicitacaoturmas.html", {"request": request})

# ---------- SOLICITAÇÃO DE ASSOCIAÇÃO ----------
@router.post("/request_association")
def request_association(payload: dict):
    if "professor_id" not in payload or "turma_id" not in payload:
        raise HTTPException(400, "professor_id e turma_id obrigatórios")
    reqs = json.loads(DATA_REQ_FILE.read_text())
    new_req = {
        "request_id": str(uuid4()),
        "professor_id": int(payload["professor_id"]),
        "turma_id": int(payload["turma_id"]),
        "message": payload.get("message",""),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    reqs.append(new_req)
    DATA_REQ_FILE.write_text(json.dumps(reqs, indent=2))
    return {"status": "created", "request_id": new_req["request_id"]}

@router.get("/my_requests/{professor_id}")
def my_requests(professor_id:int):
    reqs = json.loads(DATA_REQ_FILE.read_text())
    mine = [r for r in reqs if r.get("professor_id") == professor_id]
    return mine

@router.delete("/cancel_request")
def cancel_request(payload: dict):
    if "request_id" not in payload or "professor_id" not in payload:
        raise HTTPException(400, "request_id e professor_id obrigatórios")
    reqs = json.loads(DATA_REQ_FILE.read_text())
    new = [r for r in reqs if not (r.get("request_id")==payload["request_id"] and r.get("professor_id")==payload["professor_id"])]
    DATA_REQ_FILE.write_text(json.dumps(new, indent=2))
    return {"status":"cancelled"}
# ---------- ROTA RAIZ ----------
@router.get("/", response_class=HTMLResponse)
def professor_index(request: Request):
    """
    Página inicial do professor
    """
    return templates.TemplateResponse("solicitacaoturmas.html", {"request": request})
