# seed_db.py
from app.database import init_db, SessionLocal
from app import models
from sqlalchemy.exc import IntegrityError

def seed():
    print("Inicializando DB (create_all)...")
    init_db()

    db = SessionLocal()
    try:
        # --- SALA ---
        sala = db.query(models.Sala).filter(models.Sala.nome == "Lab1").first()
        if not sala:
            sala = models.Sala(nome="Lab1", capacidade=30, tem_computador=True)
            db.add(sala)
            db.flush()  # popula sala.id antes do commit
            print("Criada sala Lab1 id=", sala.id)
        else:
            print("Sala já existe id=", sala.id)

        # --- PROFESSOR ---
        prof = db.query(models.Professor).filter(models.Professor.nome == "Prof Teste").first()
        if not prof:
            prof = models.Professor(nome="Prof Teste", disciplinas_aptas="TINF101")
            db.add(prof)
            db.flush()
            print("Criado professor id=", prof.id)
        else:
            print("Professor já existe id=", prof.id)

        # --- TURMA ---
        turma = db.query(models.Turma).filter(models.Turma.codigo == "TINF101").first()
        if not turma:
            turma = models.Turma(
                codigo="TINF101",
                carga_horaria=60,
                precisa_computador=True,
                sala_id=sala.id,
                semestre="2025.2"
            )
            db.add(turma)
            db.flush()
            print("Criada turma id=", turma.id)
        else:
            print("Turma já existe id=", turma.id)

        # --- ASSOCIAR PROFESSOR <-> TURMA (many-to-many) ---
        # use relacionamento ORM para manter integridade
        if prof not in turma.professores:
            turma.professores.append(prof)
            print("Associado professor -> turma")
        else:
            print("Associação professor->turma já existe")

        # --- ALUNO (opcional para testar /aluno/) ---
        aluno = db.query(models.Aluno).filter(models.Aluno.matricula == "20250001").first()
        if not aluno:
            aluno = models.Aluno(nome="Aluno Teste", matricula="20250001", curso="TI")
            db.add(aluno)
            db.flush()
            print("Criado aluno id=", aluno.id)
        else:
            print("Aluno já existe id=", aluno.id)

        db.commit()
        print("Seed concluído com sucesso.")
    except IntegrityError as e:
        db.rollback()
        print("IntegrityError:", e)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
