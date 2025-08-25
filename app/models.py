from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Sala(Base):
    __tablename__ = "salas"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    capacidade = Column(Integer)
    tem_computador = Column(Boolean, default=False)

class Professor(Base):
    __tablename__ = "professores"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)

class Turma(Base):
    __tablename__ = "turmas"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, index=True)
    numero_alunos = Column(Integer)
    precisa_computador = Column(Boolean, default=False)
    professor_id = Column(Integer, ForeignKey("professores.id"))
    professor = relationship("Professor")
