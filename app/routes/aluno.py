# app/routes/aluno.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from typing import Set

router = APIRouter(prefix="/aluno", tags=["aluno"])
templates = Jinja2Templates(directory="app/templates")

# --- Conexão com banco ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Horários válidos ---
VALID_BLOCKS = {
    "M12", "M34", "M56",
    "T12", "T34", "T56",
    "N12", "N34",
    "M1234", "T1234", "N1234",
    "S12"
}

def normalize_block(b: str) -> str:
    if not isinstance(b, str):
        return ""
    return b.strip().upper().replace(" ", "")

def is_valid_block(b: str) -> bool:
    return normalize_block(b) in VALID_BLOCKS

# ---------- Rota: questionário ----------
@router.get("/", response_class=HTMLResponse)
def aluno_questionario(request: Request, db: Session = Depends(get_db), aluno_id: int = 1, semestre: str = None):
    aluno = db.get(models.Aluno, aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    query = db.query(models.Turma)
    if semestre:
        query = query.filter(models.Turma.semestre == semestre)

    disciplinas_semestre = query.all()
    return templates.TemplateResponse("aluno.html", {
        "request": request,
        "aluno": aluno,
        "disciplinas_semestre": disciplinas_semestre
    })

# ---------- Rota: salvar expectativas ----------
@router.post("/salvar")
async def salvar_expectativa(payload: dict, db: Session = Depends(get_db)):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload inválido")

    if "aluno_id" not in payload or "disciplinas" not in payload:
        raise HTTPException(status_code=400, detail="Payload deve conter 'aluno_id' e 'disciplinas'")

    try:
        aluno_id = int(payload["aluno_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="aluno_id inválido")

    preferencias = payload["disciplinas"]
    if not isinstance(preferencias, list):
        raise HTTPException(status_code=400, detail="'disciplinas' deve ser uma lista")

    aluno = db.get(models.Aluno, aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    turma_ids_seen: Set[int] = set()
    aluno_horarios: Set[str] = set()
    total_horas = 0
    prioridade_auto = 1

    for item in preferencias:
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail="Cada item deve ser um objeto")
        if "id" not in item:
            raise HTTPException(status_code=400, detail="Cada disciplina precisa do campo 'id'")

        try:
            tid = int(item["id"])
        except Exception:
            raise HTTPException(status_code=400, detail=f"ID inválido: {item.get('id')}")

        if tid in turma_ids_seen:
            raise HTTPException(status_code=400, detail=f"Turma {tid} duplicada")

        turma = db.get(models.Turma, tid)
        if not turma:
            raise HTTPException(status_code=404, detail=f"Turma {tid} não encontrada")

        try:
            total_horas += int(turma.carga_horaria)
        except Exception:
            raise HTTPException(status_code=500, detail=f"Turma {tid} tem carga_horaria inválida")

        if total_horas > 480:
            raise HTTPException(status_code=400, detail=f"Limite de 480h excedido: {total_horas}h")

        turma_ids_seen.add(tid)

        horarios = item.get("horarios", [])
        if not isinstance(horarios, list):
            raise HTTPException(status_code=400, detail=f"'horarios' deve ser lista para a turma {tid}")

        for h in horarios:
            nh = normalize_block(h)
            if not is_valid_block(nh):
                raise HTTPException(status_code=400, detail=f"Horário inválido: {h} (turma {tid})")
            if nh in aluno_horarios:
                raise HTTPException(status_code=400, detail=f"Conflito de horário: {nh} (turma {tid})")
            aluno_horarios.add(nh)

    # persistir preferências
    db.query(models.PreferenciaAluno).filter(models.PreferenciaAluno.aluno_id == aluno_id).delete()
    for item in preferencias:
        tid = int(item["id"])
        horarios = item.get("horarios", [])
        prioridade_val = item.get("prioridade") or prioridade_auto
        if item.get("prioridade") is None:
            prioridade_auto += 1

        for h in horarios:
            pref = models.PreferenciaAluno(
                aluno_id=aluno_id,
                turma_id=tid,
                horario_preferido=normalize_block(h),
                prioridade=int(prioridade_val)
            )
            db.add(pref)
    db.commit()

    return JSONResponse({
        "status": "saved",
        "aluno_id": aluno_id,
        "total_horas": total_horas,
        "total_turmas": len(turma_ids_seen),
        "total_horarios": len(aluno_horarios)
    })

# ---------- Rota: preferências atuais ----------
@router.get("/me/{aluno_id}")
def my_preferences(aluno_id: int, db: Session = Depends(get_db)):
    aluno = db.get(models.Aluno, aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    prefs = db.query(models.PreferenciaAluno).filter(models.PreferenciaAluno.aluno_id == aluno_id).order_by(models.PreferenciaAluno.prioridade).all()
    out_map = {}
    for p in prefs:
        hor = normalize_block(p.horario_preferido)
        if p.turma_id not in out_map:
            out_map[p.turma_id] = {"id": p.turma_id, "horarios": [], "prioridade": p.prioridade}
        if hor not in out_map[p.turma_id]["horarios"]:
            out_map[p.turma_id]["horarios"].append(hor)

    return JSONResponse({
        "aluno_id": aluno_id,
        "preferencias": list(out_map.values())
    })
