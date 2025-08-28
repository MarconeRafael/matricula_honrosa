from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from pathlib import Path
import json
from datetime import datetime

router = APIRouter(prefix="/professor", tags=["professor"])
templates = Jinja2Templates(directory="app/templates")

REQUESTS_FILE = Path("data/association_requests.json")
REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
if not REQUESTS_FILE.exists():
    REQUESTS_FILE.write_text("[]")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Rota: exibir perfil do professor ----------
@router.get("/", response_class=HTMLResponse)
def professor_profile(request: Request, db: Session = Depends(get_db), professor_id: int = 1):
    professor = db.query(models.Professor).filter(models.Professor.id == professor_id).first()
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    
    # Filtro de disciplinas do semestre ativo (placeholder)
    semestre_ativo = "2025.2"  # Ajuste conforme lógica do seu sistema
    disciplinas_semestre = db.query(models.Turma).filter(models.Turma.semestre == semestre_ativo).all()

    return templates.TemplateResponse("professor.html", {
        "request": request,
        "professor": professor,
        "disciplinas_semestre": disciplinas_semestre
    })


# ---------- Rota: solicitar adição ou remoção de disciplina ----------
@router.post("/solicitar")
async def solicitar(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    # Validação básica do payload
    required_fields = ["professor_id", "disciplina_id", "acao"]
    for f in required_fields:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"{f} é obrigatório")
    
    professor_id = int(data["professor_id"])
    disciplina_id = int(data["disciplina_id"])
    acao = data["acao"]

    if acao not in ("adicionar", "remover"):
        raise HTTPException(status_code=400, detail="acao deve ser 'adicionar' ou 'remover'")

    # Verifica se professor e disciplina existem
    professor = db.query(models.Professor).get(professor_id)
    disciplina = db.query(models.Turma).get(disciplina_id)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    if not disciplina:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")

    # Carrega solicitações existentes e adiciona nova
    all_requests = json.loads(REQUESTS_FILE.read_text())
    request_id = str(len(all_requests) + 1)  # Simples ID incremental
    new_request = {
        "request_id": request_id,
        "professor_id": professor_id,
        "disciplina_id": disciplina_id,
        "acao": acao,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    all_requests.append(new_request)

    # Escreve de forma atômica
    REQUESTS_FILE.write_text(json.dumps(all_requests, indent=2))

    return JSONResponse({
        "status": "ok",
        "mensagem": "Solicitação enviada para coordenação.",
        "request_id": request_id
    })
