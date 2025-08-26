from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.routes import aluno, coord, professor, view

app = FastAPI(title="API Pré-Matrícula Honrosa")

# Registrando routers
app.include_router(aluno.router)
app.include_router(coord.router)
app.include_router(professor.router)
app.include_router(view.router)

# Configurando Jinja2 para templates
templates = Jinja2Templates(directory="app/templates")

# Rota para a página inicial
@app.get("/", response_class=None)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
