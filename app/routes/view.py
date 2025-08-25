from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from collections import defaultdict
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/view", tags=["view"])

# Configura Jinja2 para servir HTML do static/
templates = Jinja2Templates(directory="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- ROTA HTML ----------
@router.get("/expectativa/html")
def view_expectativa(request: Request):
    """
    Renderiza a tela de expectativa perfeita de oferta de turmas.
    """
    return templates.TemplateResponse("expectativaperfeita.html", {"request": request})

# ---------- API JSON ----------
@router.get("/expectativa")
def expectativa_aggregada(db: Session = Depends(get_db)):
    """
    Retorna agregação simples das preferências atuais:
      - para cada turma + horario_preferido: quantidade de alunos que pediram
    Isso funciona como placeholder até a integração completa com o solver.
    """
    prefs = db.query(models.PreferenciaAluno).all()
    summary = defaultdict(lambda: {"count":0, "alunos": []})
    for p in prefs:
        key = f"{p.turma_id}__{p.horario_preferido}"
        summary[key]["count"] += 1
        summary[key]["alunos"].append(p.aluno_id)
    # monta formato legível
    out = []
    for k, v in summary.items():
        turma_id, horario = k.split("__", 1)
        t = db.query(models.Turma).get(int(turma_id))
        out.append({
            "turma_id": int(turma_id),
            "turma_codigo": t.codigo if t else None,
            "horario_preferido": horario,
            "count": v["count"],
            "alunos": v["alunos"]
        })
    # ordena por demanda decrescente
    out = sorted(out, key=lambda x: x["count"], reverse=True)
    return {"aggregated_preferences": out}
