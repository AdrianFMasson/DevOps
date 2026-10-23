from routes.user_rota import obter_usuario_autenticado
from db.db import database
from pathlib import Path

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from jwt import InvalidTokenError
from datetime import datetime
from db.db import database
from entities.models import User, PerfilUsuario
from utils.seguranca import decodificar_token



@app.get("/dashboard-admin", include_in_schema=False)
def dashboard_gestor(
    request: Request,
    db: Session = Depends(database.get_db)
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        resposta = RedirectResponse(
            url="/login",
            status_code=status.HTTP_303_SEE_OTHER
        )
        resposta.delete_cookie("access_token", path="/")
        return resposta

    if autenticacao["perfil"] != PerfilUsuario.ADMINISTRADOR:
        if autenticacao["perfil"] == PerfilUsuario.OPERADOR:
            return RedirectResponse(
                url="/dashboard-user",
                status_code=status.HTTP_303_SEE_OTHER
            )

        return RedirectResponse(
            url="/login",
            status_code=status.HTTP_303_SEE_OTHER
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context={
            "usuario": autenticacao["usuario"],
            "ano_atual": datetime.now().year
        }
    )
