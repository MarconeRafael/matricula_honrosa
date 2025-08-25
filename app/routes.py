# app/routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from .solver import solve_sample
import csv
from io import StringIO
from typing import Dict

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/import/turmas")
async def import_turmas(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    s = StringIO(content.decode())
    reader = csv.DictReader(s)
    for row in reader:
        t = models.Turma(codigo=row["codigo"], numero_alunos=int(row["numero_alunos"]),
                         precisa_computador=row.get("precisa_computador","False") in ["True","true","1"])
        db.add(t)
    db.commit()
    return {"imported": True}

# --- novos endpoints para o frontend de teste ---
@router.get("/test-solve")
def test_solve():
    # mesma instância que usamos no run_solver.py
    salas = [
        {"id": 1, "nome": "Sala A", "capacidade": 40, "tem_computador": True},
        {"id": 2, "nome": "Sala B", "capacidade": 25, "tem_computador": False},
        {"id": 3, "nome": "Lab TI", "capacidade": 20, "tem_computador": True},
    ]
    professors = [
        {"id": 1, "nome": "Prof A"},
        {"id": 2, "nome": "Prof B"},
    ]
    timeslots = [
        {"id": 1, "descricao": "Segunda/M1"},
        {"id": 2, "descricao": "Segunda/M2"},
        {"id": 3, "descricao": "Terca/M1"},
    ]
    turmas = [
        {"id": 101, "codigo": "BCC101", "numero_alunos": 30, "precisa_computador": False, "professor_id": 1},
        {"id": 102, "codigo": "BCC102", "numero_alunos": 20, "precisa_computador": True, "professor_id": 1},
        {"id": 103, "codigo": "BCC103", "numero_alunos": 18, "precisa_computador": True, "professor_id": 2},
    ]
    weights = {101: 0, 102: 10, 103: 1}

    ok, allocs, status = solve_sample(turmas, salas, timeslots, professors, turma_weights=weights, time_limit=5)
    if not ok:
        raise HTTPException(status_code=400, detail={"status": status, "reason": allocs})
    return {"status": status, "allocations": allocs, "turmas": turmas, "salas": salas, "timeslots": timeslots}

@router.post("/solve")
def solve_endpoint(payload: Dict):
    # payload esperado: {turmas: [...], salas: [...], timeslots: [...], professors: [...], turma_weights: {...} (opcional)}
    try:
        turmas = payload["turmas"]
        salas = payload["salas"]
        timeslots = payload["timeslots"]
        professors = payload["professors"]
        turma_weights = payload.get("turma_weights")
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido. Verifique chaves obrigatórias.")

    ok, allocs, status = solve_sample(turmas, salas, timeslots, professors, turma_weights=turma_weights, time_limit=10)
    if not ok:
        raise HTTPException(status_code=400, detail={"status": status, "reason": allocs})
    return {"status": status, "allocations": allocs}
