from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
import json
from pathlib import Path
from datetime import datetime

from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/coord", tags=["coord"])

# Configura Jinja2 para servir HTML do static/
templates = Jinja2Templates(directory="static")

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
@router.get("/cadastro", response_class=HTMLResponse)
def cadastro_turmas(request: Request):
    """
    Renderiza a tela de cadastro de possíveis turmas.
    """
    return templates.TemplateResponse("cadastro_associação_turmas.html", {"request": request})

# ---------- CRUD TURMAS ----------
@router.get("/turmas")
def list_turmas(db: Session = Depends(get_db)):
    turmas = db.query(models.Turma).all()
    result = []
    for t in turmas:
        result.append({
            "id": t.id,
            "codigo": t.codigo,
            "carga_horaria": t.carga_horaria,
            "precisa_computador": t.precisa_computador,
            "professores": [{"id": p.id, "nome": p.nome} for p in t.professores],
            "sala_id": t.sala_id
        })
    return result

@router.post("/turma")
def create_turma(payload: dict, db: Session = Depends(get_db)):
    if "codigo" not in payload or "carga_horaria" not in payload:
        raise HTTPException(400, "Payload inválido: codigo e carga_horaria obrigatórios")
    t = models.Turma(
        codigo=payload["codigo"],
        carga_horaria=int(payload["carga_horaria"]),
        precisa_computador=bool(payload.get("precisa_computador", False)),
        sala_id=payload.get("sala_id")
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"status": "created", "id": t.id}

@router.put("/turma/{turma_id}")
def update_turma(turma_id: int, payload: dict, db: Session = Depends(get_db)):
    t = db.query(models.Turma).get(turma_id)
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    for k in ("codigo", "carga_horaria", "precisa_computador", "sala_id"):
        if k in payload:
            setattr(t, "carga_horaria" if k=="carga_horaria" else k, payload[k])
    db.commit()
    return {"status": "updated"}

@router.delete("/turma/{turma_id}")
def delete_turma(turma_id:int, db: Session = Depends(get_db)):
    t = db.query(models.Turma).get(turma_id)
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    db.delete(t)
    db.commit()
    return {"status": "deleted"}

# ---------- CRUD PROFESSORES ----------
@router.get("/professores")
def list_professores(db: Session = Depends(get_db)):
    profs = db.query(models.Professor).all()
    return [{"id": p.id, "nome": p.nome, "disciplinas_aptas": p.disciplinas_aptas} for p in profs]

@router.post("/professor")
def create_professor(payload: dict, db: Session = Depends(get_db)):
    if "nome" not in payload:
        raise HTTPException(400, "nome é obrigatório")
    p = models.Professor(nome=payload["nome"], disciplinas_aptas=payload.get("disciplinas_aptas",""))
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"status":"created", "id": p.id}

@router.put("/professor/{prof_id}")
def update_professor(prof_id:int, payload:dict, db: Session = Depends(get_db)):
    p = db.query(models.Professor).get(prof_id)
    if not p:
        raise HTTPException(404, "Professor não encontrado")
    if "nome" in payload: p.nome = payload["nome"]
    if "disciplinas_aptas" in payload: p.disciplinas_aptas = payload["disciplinas_aptas"]
    db.commit()
    return {"status":"updated"}

@router.delete("/professor/{prof_id}")
def delete_professor(prof_id:int, db: Session = Depends(get_db)):
    p = db.query(models.Professor).get(prof_id)
    if not p:
        raise HTTPException(404, "Professor não encontrado")
    db.delete(p)
    db.commit()
    return {"status":"deleted"}

# ---------- CRUD SALAS ----------
@router.get("/salas")
def list_salas(db: Session = Depends(get_db)):
    salas = db.query(models.Sala).all()
    return [{"id": s.id, "nome": s.nome, "capacidade": s.capacidade, "tem_computador": s.tem_computador} for s in salas]

@router.post("/sala")
def create_sala(payload: dict, db: Session = Depends(get_db)):
    if "nome" not in payload or "capacidade" not in payload:
        raise HTTPException(400, "nome e capacidade obrigatórios")
    s = models.Sala(nome=payload["nome"], capacidade=int(payload["capacidade"]), tem_computador=bool(payload.get("tem_computador", False)))
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"status":"created", "id": s.id}

@router.put("/sala/{sala_id}")
def update_sala(sala_id:int, payload:dict, db: Session = Depends(get_db)):
    s = db.query(models.Sala).get(sala_id)
    if not s:
        raise HTTPException(404, "Sala não encontrada")
    if "nome" in payload: s.nome = payload["nome"]
    if "capacidade" in payload: s.capacidade = int(payload["capacidade"])
    if "tem_computador" in payload: s.tem_computador = bool(payload["tem_computador"])
    db.commit()
    return {"status":"updated"}

@router.delete("/sala/{sala_id}")
def delete_sala(sala_id:int, db: Session = Depends(get_db)):
    s = db.query(models.Sala).get(sala_id)
    if not s:
        raise HTTPException(404, "Sala não encontrada")
    db.delete(s)
    db.commit()
    return {"status":"deleted"}

# ---------- ASSOCIAR / REMOVER PROFESSOR DE TURMA ----------
@router.post("/turma/{turma_id}/add_professor")
def add_professor_to_turma(turma_id:int, payload: dict, db: Session = Depends(get_db)):
    if "professor_id" not in payload:
        raise HTTPException(400, "professor_id obrigatório")
    p = db.query(models.Professor).get(int(payload["professor_id"]))
    t = db.query(models.Turma).get(turma_id)
    if not p or not t:
        raise HTTPException(404, "Professor ou Turma não encontrada")
    if p not in t.professores:
        t.professores.append(p)
        db.commit()
    return {"status":"associated"}

@router.delete("/turma/{turma_id}/remove_professor")
def remove_professor_from_turma(turma_id:int, payload: dict, db: Session = Depends(get_db)):
    if "professor_id" not in payload:
        raise HTTPException(400, "professor_id obrigatório")
    p = db.query(models.Professor).get(int(payload["professor_id"]))
    t = db.query(models.Turma).get(turma_id)
    if not p or not t:
        raise HTTPException(404, "Professor ou Turma não encontrada")
    if p in t.professores:
        t.professores.remove(p)
        db.commit()
    return {"status":"removed"}

# ---------- SOLICITAÇÕES ----------
@router.get("/requests")
def list_requests():
    raw = json.loads(DATA_REQ_FILE.read_text())
    return raw

@router.post("/requests/review")
def review_request(payload: dict, db: Session = Depends(get_db)):
    if "request_id" not in payload or "action" not in payload:
        raise HTTPException(400, "request_id e action obrigatórios")
    reqs = json.loads(DATA_REQ_FILE.read_text())
    found = next((r for r in reqs if r.get("request_id")==payload["request_id"]), None)
    if not found:
        raise HTTPException(404, "Request não encontrada")
    action = payload["action"]
    if action not in ("approve","deny"):
        raise HTTPException(400, "action deve ser 'approve' ou 'deny'")
    found["status"] = action
    found["reviewed_at"] = datetime.utcnow().isoformat()
    DATA_REQ_FILE.write_text(json.dumps(reqs, indent=2))
    if action == "approve":
        prof_id = int(found["professor_id"])
        turma_id = int(found["turma_id"])
        p = db.query(models.Professor).get(prof_id)
        t = db.query(models.Turma).get(turma_id)
        if not p or not t:
            raise HTTPException(404, "Professor ou turma não encontrada para associação")
        if p not in t.professores:
            t.professores.append(p)
            db.commit()
    return {"status": "reviewed", "action": action}
