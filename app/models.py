from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# ---------- MODELO SALA ----------
class Sala(Base):
    __tablename__ = "salas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    capacidade = Column(Integer, nullable=False)
    tem_computador = Column(Boolean, default=False)

    # Relacionamento inverso
    turmas = relationship("Turma", back_populates="sala")


# ---------- MODELO PROFESSOR ----------
class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    disciplinas_aptas = Column(String, default="")  # ex: lista de códigos separados por vírgula

    # Relacionamento muitos-para-muitos com Turma
    turmas = relationship(
        "Turma",
        secondary="professor_turma",
        back_populates="professores"
    )


# ---------- TABELA ASSOCIATIVA PROFESSOR-TURMA ----------
professor_turma = Table(
    "professor_turma",
    Base.metadata,
    Column("professor_id", Integer, ForeignKey("professores.id"), primary_key=True),
    Column("turma_id", Integer, ForeignKey("turmas.id"), primary_key=True)
)


# ---------- MODELO TURMA ----------
class Turma(Base):
    __tablename__ = "turmas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, nullable=False)
    carga_horaria = Column(Integer, nullable=False)
    precisa_computador = Column(Boolean, default=False)
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=True)
    semestre = Column(String, default="2025.2")  # placeholder para semestre ativo

    sala = relationship("Sala", back_populates="turmas")
    professores = relationship(
        "Professor",
        secondary="professor_turma",
        back_populates="turmas"
    )


# ---------- MODELO ALUNO ----------
class Aluno(Base):
    __tablename__ = "alunos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    matricula = Column(String, unique=True, nullable=False)
    curso = Column(String, nullable=True)

    # Relacionamento com preferências
    preferencias = relationship("PreferenciaAluno", back_populates="aluno", cascade="all, delete-orphan")


# ---------- MODELO PREFERENCIA DO ALUNO ----------
class PreferenciaAluno(Base):
    __tablename__ = "preferencias_alunos"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    horario_preferido = Column(String, nullable=False)
    prioridade = Column(Integer, default=1)

    turma = relationship("Turma")
    aluno = relationship("Aluno", back_populates="preferencias")
