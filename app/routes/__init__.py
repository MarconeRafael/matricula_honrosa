# app/routes/__init__.py
# Tornar os módulos de rota importáveis via "from app.routes import ..."

from . import aluno, coord, professor, view

__all__ = ["aluno", "coord", "professor", "view"]
