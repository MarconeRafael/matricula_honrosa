from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pré-Matrícula")
app.include_router(router, prefix="/api")
