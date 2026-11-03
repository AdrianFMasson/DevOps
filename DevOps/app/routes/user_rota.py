from pathlib import Path
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from db.db import database
from entities.models import User, PerfilUsuario
from utils.seguranca import (
    decodificar_token,
    verificar_token_revogado,
)


rota_user = APIRouter()

DIRETORIO_TEMPLATES = (
    Path(__file__).resolve().parent.parent / "templates"
)

templates = Jinja2Templates(
    directory=str(DIRETORIO_TEMPLATES)
)


# =========================================================
# CABEÇALHOS DE RESPOSTA
# =========================================================

def aplicar_cabecalhos_sem_cache(resposta):
    resposta.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, max-age=0"
    )
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["Expires"] = "0"

    return resposta


# =========================================================
# VALIDAÇÃO CENTRAL DO TOKEN
# =========================================================

def obter_usuario_autenticado(
    request: Request,
    db: Session,
):
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        # 1. Validar assinatura, expiração e tipo do JWT.
        payload = decodificar_token(
            token,
            tipo_esperado="access",
        )

        # 2. Obter o identificador do usuário.
        id_usuario = int(payload["sub"])

        # 3. Verificar se o token foi revogado.
        if verificar_token_revogado(payload, db):
            return None

    except (
        ValueError,
        KeyError,
        TypeError,
    ):
        return None

    # 4. Verificar se o usuário ainda existe.
    usuario = db.get(
        User,
        id_usuario,
    )

    if usuario is None:
        return None

    # 5. Verificar se o usuário continua ativo.
    if not usuario.ativo:
        return None

    return {
        "usuario": usuario,
        "perfil": usuario.perfil,
    }


# =========================================================
# VERIFICAÇÃO DE OPERADOR
# =========================================================

def verificar_operador(
    request: Request,
    db: Session,
):
    autenticacao = obter_usuario_autenticado(
        request,
        db,
    )

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != PerfilUsuario.OPERADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


# =========================================================
# VERIFICAÇÃO DE ADMINISTRADOR
# =========================================================

def verificar_administrador(
    request: Request,
    db: Session,
):
    autenticacao = obter_usuario_autenticado(
        request,
        db,
    )

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != PerfilUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente ao administrador.",
        )

    return autenticacao


# =========================================================
# REDIRECIONAR PARA LOGIN
# =========================================================

def redirecionar_login(request: Request):
    resposta = RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    # Utiliza a mesma configuração de segurança do cookie
    # definida no momento do login.
    cookie_seguro = request.url.scheme == "https"

    resposta.delete_cookie(
        key="access_token",
        path="/",
        secure=cookie_seguro,
        httponly=True,
        samesite="lax",
    )

    resposta.delete_cookie(
        key="refresh_token",
        path="/",
        secure=cookie_seguro,
        httponly=True,
        samesite="lax",
    )

    return aplicar_cabecalhos_sem_cache(resposta)


# =========================================================
# DASHBOARD DO OPERADOR
# =========================================================

@rota_user.get("/dashboard-user")
def dashboard_user(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(
        request,
        db,
    )

    if autenticacao is None:
        return redirecionar_login(request)

    resposta = templates.TemplateResponse(
        request=request,
        name="dashboard_user.html",
        context={
            "usuario": autenticacao["usuario"],
            "ano_atual": datetime.now().year,
        },
    )

    return aplicar_cabecalhos_sem_cache(resposta)


# =========================================================
# PÁGINA DE VEÍCULOS DO OPERADOR
# =========================================================

@rota_user.get("/user/veiculos")
def pagina_veiculos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(
        request,
        db,
    )

    if autenticacao is None:
        return redirecionar_login(request)

    resposta = templates.TemplateResponse(
        request=request,
        name="veiculos.html",
        context={
            "usuario": autenticacao["usuario"],
            "eh_admin": False,
            "ano_atual": datetime.now().year,
        },
    )

    return aplicar_cabecalhos_sem_cache(resposta)


# =========================================================
# PÁGINA DE VAGAS DO OPERADOR
# =========================================================

@rota_user.get("/user/vagas")
def pagina_vagas(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(
        request,
        db,
    )

    if autenticacao is None:
        return redirecionar_login(request)

    resposta = templates.TemplateResponse(
        request=request,
        name="vagas.html",
        context={
            "usuario": autenticacao["usuario"],
            "eh_admin": False,
            "ano_atual": datetime.now().year,
        },
    )

    return aplicar_cabecalhos_sem_cache(resposta)


# =========================================================
# PÁGINA DE CLIENTES DO OPERADOR
# =========================================================

@rota_user.get("/user/clientes")
def pagina_clientes(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = verificar_operador(
        request,
        db,
    )

    if autenticacao is None:
        return redirecionar_login(request)

    resposta = templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context={
            "usuario": autenticacao["usuario"],
            "eh_admin": False,
            "ano_atual": datetime.now().year,
        },
    )

    return aplicar_cabecalhos_sem_cache(resposta)