
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from db.db import database
from entities.models import PerfilUsuario
from routes.user_rota import obter_usuario_autenticado


admin_rota = APIRouter()

DIRETORIO_TEMPLATES = (
    Path(__file__).resolve().parent.parent / "templates"
)

templates = Jinja2Templates(
    directory=str(DIRETORIO_TEMPLATES)
)


@admin_rota.get("/dashboard-admin", include_in_schema=False)
def dashboard_gestor(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        resposta = RedirectResponse(
            url="/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )
        resposta.delete_cookie("access_token", path="/")
        return resposta

    if autenticacao["perfil"] != PerfilUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente ao administrador.",
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context={
            "usuario": autenticacao["usuario"],
            "ano_atual": datetime.now().year,
        },
    )
