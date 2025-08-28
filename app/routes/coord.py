from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import json

from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/coord", tags=["coord"])
templates = Jinja2Templates(directory="app/templates")

# JSON persistente para requests de associação
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
    return templates.TemplateResponse("coord.html", {"request": request})


# ---------- CRUD TURMAS ----------
@router.get("/turmas")
def list_turmas(semestre: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Lista turmas. Pode filtrar por semestre se fornecido.
    """
    query = db.query(models.Turma)
    if semestre:
        query = query.filter(models.Turma.semestre == semestre)
    turmas = query.all()
    return [{"id": t.id,
             "codigo": t.codigo,
             "carga_horaria": t.carga_horaria,
             "precisa_computador": t.precisa_computador,
             "professores": [{"id": p.id, "nome": p.nome} for p in t.professores],
             "sala_id": t.sala_id} for t in turmas]

@router.post("/turmas")
def create_turma(payload: dict, db: Session = Depends(get_db)):
    """
    Cria uma nova turma com validação de payload.
    """
    codigo = payload.get("codigo")
    carga_horaria = payload.get("carga_horaria")
    sala_id = payload.get("sala_id")
    precisa_computador = payload.get("precisa_computador", False)

    if not codigo or carga_horaria is None:
        raise HTTPException(400, "Payload inválido: codigo e carga_horaria obrigatórios")

    try:
        carga_horaria = int(carga_horaria)
        if carga_horaria <= 0:
            raise ValueError()
    except ValueError:
        raise HTTPException(400, "carga_horaria deve ser inteiro positivo")

    if sala_id:
        sala = db.query(models.Sala).get(sala_id)
        if not sala:
            raise HTTPException(404, "Sala não encontrada")
    turma = models.Turma(codigo=codigo, carga_horaria=carga_horaria,
                         precisa_computador=bool(precisa_computador),
                         sala_id=sala_id)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return {"status": "created", "id": turma.id}


@router.put("/turmas/{turma_id}")
def update_turma(turma_id: int, payload: dict, db: Session = Depends(get_db)):
    t = db.query(models.Turma).get(turma_id)
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    if "codigo" in payload: t.codigo = payload["codigo"]
    if "carga_horaria" in payload:
        try:
            ch = int(payload["carga_horaria"])
            if ch <= 0: raise ValueError()
            t.carga_horaria = ch
        except ValueError:
            raise HTTPException(400, "carga_horaria deve ser inteiro positivo")
    if "precisa_computador" in payload: t.precisa_computador = bool(payload["precisa_computador"])
    if "sala_id" in payload:
        sala = db.query(models.Sala).get(payload["sala_id"])
        if not sala:
            raise HTTPException(404, "Sala não encontrada")
        t.sala_id = payload["sala_id"]
    db.commit()
    return {"status": "updated", "id": t.id}


@router.delete("/turmas/{turma_id}")
def delete_turma(turma_id:int, db: Session = Depends(get_db)):
    t = db.query(models.Turma).get(turma_id)
    if not t:
        raise HTTPException(404, "Turma não encontrada")
    db.delete(t)
    db.commit()
    return {"status": "deleted", "id": turma_id}


# ---------- CRUD PROFESSORES ----------
@router.get("/professores")
def list_professores(db: Session = Depends(get_db)):
    profs = db.query(models.Professor).all()
    return [{"id": p.id, "nome": p.nome, "disciplinas_aptas": p.disciplinas_aptas} for p in profs]

@router.post("/professores")
def create_professor(payload: dict, db: Session = Depends(get_db)):
    nome = payload.get("nome")
    disciplinas_aptas = payload.get("disciplinas_aptas", "")
    if not nome:
        raise HTTPException(400, "nome é obrigatório")
    p = models.Professor(nome=nome, disciplinas_aptas=disciplinas_aptas)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"status":"created", "id": p.id}

@router.put("/professores/{prof_id}")
def update_professor(prof_id:int, payload:dict, db: Session = Depends(get_db)):
    p = db.query(models.Professor).get(prof_id)
    if not p:
        raise HTTPException(404, "Professor não encontrado")
    if "nome" in payload: p.nome = payload["nome"]
    if "disciplinas_aptas" in payload: p.disciplinas_aptas = payload["disciplinas_aptas"]
    db.commit()
    return {"status":"updated", "id": p.id}

@router.delete("/professores/{prof_id}")
def delete_professor(prof_id:int, db: Session = Depends(get_db)):
    p = db.query(models.Professor).get(prof_id)
    if not p:
        raise HTTPException(404, "Professor não encontrado")
    db.delete(p)
    db.commit()
    return {"status":"deleted", "id": prof_id}


# ---------- CRUD SALAS ----------
@router.get("/salas")
def list_salas(db: Session = Depends(get_db)):
    salas = db.query(models.Sala).all()
    return [{"id": s.id, "nome": s.nome, "capacidade": s.capacidade, "tem_computador": s.tem_computador} for s in salas]

@router.post("/salas")
def create_sala(payload: dict, db: Session = Depends(get_db)):
    nome = payload.get("nome")
    capacidade = payload.get("capacidade")
    tem_computador = payload.get("tem_computador", False)
    if not nome or capacidade is None:
        raise HTTPException(400, "nome e capacidade obrigatórios")
    try:
        capacidade = int(capacidade)
        if capacidade <= 0: raise ValueError()
    except ValueError:
        raise HTTPException(400, "capacidade deve ser inteiro positivo")
    s = models.Sala(nome=nome, capacidade=capacidade, tem_computador=bool(tem_computador))
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"status":"created", "id": s.id}

@router.put("/salas/{sala_id}")
def update_sala(sala_id:int, payload:dict, db: Session = Depends(get_db)):
    s = db.query(models.Sala).get(sala_id)
    if not s:
        raise HTTPException(404, "Sala não encontrada")
    if "nome" in payload: s.nome = payload["nome"]
    if "capacidade" in payload:
        try:
            cap = int(payload["capacidade"])
            if cap <= 0: raise ValueError()
            s.capacidade = cap
        except ValueError:
            raise HTTPException(400, "capacidade deve ser inteiro positivo")
    if "tem_computador" in payload: s.tem_computador = bool(payload["tem_computador"])
    db.commit()
    return {"status":"updated", "id": s.id}

@router.delete("/salas/{sala_id}")
def delete_sala(sala_id:int, db: Session = Depends(get_db)):
    s = db.query(models.Sala).get(sala_id)
    if not s:
        raise HTTPException(404, "Sala não encontrada")
    db.delete(s)
    db.commit()
    return {"status":"deleted", "id": sala_id}


# ---------- ASSOCIAR / REMOVER PROFESSOR DE TURMA ----------
@router.post("/turmas/{turma_id}/add_professor")
def add_professor_to_turma(turma_id:int, payload: dict, db: Session = Depends(get_db)):
    prof_id = payload.get("professor_id")
    if not prof_id:
        raise HTTPException(400, "professor_id obrigatório")
    t = db.query(models.Turma).get(turma_id)
    p = db.query(models.Professor).get(prof_id)
    if not t or not p:
        raise HTTPException(404, "Professor ou Turma não encontrada")
    if p not in t.professores:
        t.professores.append(p)
        db.commit()
    return {"status":"associated", "turma_id": turma_id, "professor_id": prof_id}

@router.delete("/turmas/{turma_id}/remove_professor")
def remove_professor_from_turma(turma_id:int, payload: dict, db: Session = Depends(get_db)):
    prof_id = payload.get("professor_id")
    if not prof_id:
        raise HTTPException(400, "professor_id obrigatório")
    t = db.query(models.Turma).get(turma_id)
    p = db.query(models.Professor).get(prof_id)
    if not t or not p:
        raise HTTPException(404, "Professor ou Turma não encontrada")
    if p in t.professores:
        t.professores.remove(p)
        db.commit()
    return {"status":"removed", "turma_id": turma_id, "professor_id": prof_id}


# ---------- SOLICITAÇÕES ----------
@router.get("/requests")
def list_requests():
    raw = json.loads(DATA_REQ_FILE.read_text())
    return raw

@router.post("/requests/review")
def review_request(payload: dict, db: Session = Depends(get_db)):
    req_id = payload.get("request_id")
    action = payload.get("action")
    if not req_id or not action:
        raise HTTPException(400, "request_id e action obrigatórios")
    if action not in ("approve","deny"):
        raise HTTPException(400, "action deve ser 'approve' ou 'deny'")

    # Carregar e modificar JSON apenas se tudo estiver correto
    reqs = json.loads(DATA_REQ_FILE.read_text())
    found = next((r for r in reqs if r.get("request_id")==req_id), None)
    if not found:
        raise HTTPException(404, "Request não encontrada")

    found["status"] = action
    found["reviewed_at"] = datetime.utcnow().isoformat()

    if action == "approve":
        prof_id = int(found["professor_id"])
        turma_id = int(found["turma_id"])
        p = db.query(models.Professor).get(prof_id)
        t = db.query(models.Turma).get(turma_id)
        if not p or not t:
            raise HTTPException(404, "Professor ou turma não encontrada para associação")
        if p not in t.professores:
            t.professores.append(p)
        db.commit()  # commit único
    # Salvar JSON após sucesso no DB
    DATA_REQ_FILE.write_text(json.dumps(reqs, indent=2))
    return {"status": "reviewed", "action": action, "request_id": req_id}


# ---------- ROTA RAIZ ----------
@router.get("/", response_class=HTMLResponse)
def coord_index(request: Request):
    """
    Página inicial do coordenador
    """
    return templates.TemplateResponse("coord.html", {"request": request})
