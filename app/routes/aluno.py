from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

router = APIRouter(prefix="/aluno", tags=["aluno"])

# Configura Jinja2 para servir HTML do templates/
templates = Jinja2Templates(directory="app/templates")  # criar pasta app/templates com HTML

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota para servir a tela de questionário interativo
@router.get("/questionario", response_class=HTMLResponse)
def questionario(request: Request):
    return templates.TemplateResponse("questionariointerativo.html", {"request": request})

# Rota para salvar expectativas de turmas do aluno
@router.post("/expectativa")
def submit_expectativa(payload: dict, db: Session = Depends(get_db)):
    if "aluno_id" not in payload or "preferencias" not in payload:
        raise HTTPException(status_code=400, detail="Payload inválido")

    aluno_id = int(payload["aluno_id"])
    prefs = payload["preferencias"]
    aluno = db.get(models.Aluno, aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # calcula soma de carga_horaria considerando cada turma apenas uma vez
    turma_ids = set()
    total_horas = 0
    for p in prefs:
        tid = int(p["turma_id"])
        if tid not in turma_ids:
            turma = db.get(models.Turma, tid)
            if not turma:
                raise HTTPException(status_code=404, detail=f"Turma {tid} não encontrada")
            total_horas += int(turma.carga_horaria)
            turma_ids.add(tid)

    if total_horas > 480:
        raise HTTPException(status_code=400, detail=f"Limite excedido: carga total {total_horas}h > 480h")

    # limpa preferências antigas do aluno e grava as novas
    db.query(models.PreferenciaAluno).filter(models.PreferenciaAluno.aluno_id == aluno_id).delete()
    for p in prefs:
        pref = models.PreferenciaAluno(
            aluno_id=aluno_id,
            turma_id=int(p["turma_id"]),
            horario_preferido=p.get("horario_preferido", ""),
            prioridade=int(p.get("prioridade", 1))
        )
        db.add(pref)
    db.commit()

    return {"status": "saved", "total_horas": total_horas, "count": len(prefs)}

# Rota para obter preferências de um aluno
@router.get("/me/{aluno_id}")
def my_preferences(aluno_id: int, db: Session = Depends(get_db)):
    aluno = db.get(models.Aluno, aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    
    prefs = db.query(models.PreferenciaAluno).filter(models.PreferenciaAluno.aluno_id == aluno_id).all()
    out = [
        {
            "id": p.id,
            "turma_id": p.turma_id,
            "horario_preferido": p.horario_preferido,
            "prioridade": p.prioridade
        } for p in prefs
    ]
    return {"aluno_id": aluno_id, "preferencias": out}
