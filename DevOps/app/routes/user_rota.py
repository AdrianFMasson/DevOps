
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from jwt import InvalidTokenError

from db.db import database
from entities.models import User, PerfilUsuario
from utils.seguranca import decodificar_token


rota_user = APIRouter()

DIRETORIO_TEMPLATES = (
    Path(__file__).resolve().parent.parent / "templates"
)

templates = Jinja2Templates(
    directory=str(DIRETORIO_TEMPLATES)
)


def obter_usuario_autenticado(
    request: Request,
    db: Session,
):
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = decodificar_token(
            token,
            tipo_esperado="access",
        )

        id_usuario = int(payload["sub"])

    except (
        InvalidTokenError,
        ValueError,
        KeyError,
        TypeError,
    ):
        return None

    usuario = db.get(User, id_usuario)

    if usuario is None or not usuario.ativo:
        return None

    return {
        "usuario": usuario,
        "perfil": usuario.perfil,
    }


def verificar_operador(
    request: Request,
    db: Session,
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != PerfilUsuario.OPERADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


def verificar_administrador(
    request: Request,
    db: Session,
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != PerfilUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente ao administrador.",
        )

    return autenticacao


def redirecionar_login():
    resposta = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    resposta.delete_cookie(
        "access_token",
        path="/",
    )

    return resposta


@rota_user.get("/dashboard-user")
def dashboard_user(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(request, db)

    if autenticacao is None:
        return redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="dashboard_user.html",
        context={
            "usuario": autenticacao["usuario"],
            "ano_atual": datetime.now().year,
        },
    )


@rota_user.get("/user/veiculos")
def pagina_veiculos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(request, db)

    if autenticacao is None:
        return redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="veiculos.html",
        context={
            "usuario": autenticacao["usuario"],
            "eh_admin": False,
            "ano_atual": datetime.now().year,
        },
    )


@rota_user.get("/user/vagas")
def pagina_vagas(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(request, db)

    if autenticacao is None:
        return redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="vagas.html",
        context={
            "usuario": autenticacao["usuario"],
            "eh_admin": False,
            "ano_atual": datetime.now().year,
        },
    )


@rota_user.get("/user/clientes")
def pagina_clientes(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(request, db)

    if autenticacao is None:
        return redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context={
            "usuario": autenticacao["usuario"],
            "eh_admin": False,
            "ano_atual": datetime.now().year,
        },
    )
