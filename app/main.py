# app/main.py
from fastapi import FastAPI
from .database import engine, Base
from . import models
from .routes import router
from fastapi.staticfiles import StaticFiles
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pré-Matrícula Honrosa")
app.include_router(router, prefix="/api")

# serve pasta 'static' (coloque o index.html lá)
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
