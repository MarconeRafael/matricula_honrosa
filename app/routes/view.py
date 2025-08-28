from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from collections import defaultdict
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/view", tags=["view"])

templates = Jinja2Templates(directory="app/templates")

def get_db():
    """
    Retorna uma sessão do SQLAlchemy para injeção de dependência.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ROTAS HTML ----------
@router.get("/view/html", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def view_expectativa(request: Request):
    """
    Renderiza a tela de expectativa perfeita de oferta de turmas.
    GET /view/expectativa/html e GET /view/ retornam a mesma página.
    """
    return templates.TemplateResponse("view.html", {"request": request})

# ---------- API JSON ----------
@router.get("/expectativa")
def expectativa_aggregada(db: Session = Depends(get_db)):
    """
    Retorna agregação das preferências atuais dos alunos:
      - Para cada turma e horário preferido, retorna a quantidade de alunos que solicitaram.
      - Ordena por demanda decrescente.
      - Pré-carrega todas as turmas para evitar N+1 queries.
      - Filtragem por semestre ativo pode ser adicionada futuramente.
    """
    # Carrega todas as turmas de uma vez
    turmas_dict = {t.id: t for t in db.query(models.Turma).all()}

    # Consulta todas as preferências de alunos
    prefs = db.query(models.PreferenciaAluno).all()

    summary = defaultdict(lambda: {"count": 0, "alunos": []})
    for p in prefs:
        # Validação simples para evitar dados inconsistentes
        if not p.turma_id or not p.horario_preferido:
            continue
        key = f"{p.turma_id}__{p.horario_preferido}"
        summary[key]["count"] += 1
        summary[key]["alunos"].append(p.aluno_id)

    # Monta lista legível
    out = []
    for k, v in summary.items():
        turma_id_str, horario = k.split("__", 1)
        turma_id = int(turma_id_str)
        t = turmas_dict.get(turma_id)
        out.append({
            "turma_id": turma_id,
            "turma_codigo": t.codigo if t else None,
            "horario_preferido": horario,
            "count": v["count"],
            "alunos": v["alunos"]
        })

    # Ordena por demanda decrescente
    out = sorted(out, key=lambda x: x["count"], reverse=True)

    return JSONResponse({"aggregated_preferences": out})
