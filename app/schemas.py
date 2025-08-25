from pydantic import BaseModel

class SalaCreate(BaseModel):
    nome: str
    capacidade: int
    tem_computador: bool

class TurmaCreate(BaseModel):
    codigo: str
    numero_alunos: int
    precisa_computador: bool
    professor_id: int
