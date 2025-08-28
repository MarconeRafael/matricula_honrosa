import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Usa variável de ambiente se disponível; fallback para sqlite local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Cria engine (SQLite precisa do check_same_thread)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Session maker padrão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependência para FastAPI: fornece uma sessão do DB por request.
    Uso: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Cria todas as tabelas declaradas em app.models.Base.
    Recomendo usar Alembic para migrações em produção; essa função é
    prática para desenvolvimento, testes ou inicialização em container.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Executar: python -m app.database
    print("Inicializando banco de dados e criando tabelas (se não existirem)...")
    init_db()
    print("Concluído.")
