from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
import csv
from io import StringIO

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
