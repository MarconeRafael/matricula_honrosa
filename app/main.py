from fastapi import FastAPI
from app.routes import aluno, coord, professor, view
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="API Pré-Matrícula Honrosa")

# Incluindo os routers
app.include_router(aluno.router, prefix="/aluno", tags=["Aluno"])
app.include_router(coord.router, prefix="/coord", tags=["Coord"])
app.include_router(professor.router, prefix="/professor", tags=["Professor"])
app.include_router(view.router, prefix="/view", tags=["View"])

# Serve front-end
app.mount("/", StaticFiles(directory="static", html=True), name="static")
