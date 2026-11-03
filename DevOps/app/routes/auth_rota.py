import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from db.db import database
from controller.AuthController import autenticar_usuario
from entities.models import TokenRevogado, User
from config.Config import settings

from utils.seguranca import (
    decodificar_token,
    criar_access_token,
    criar_refresh_token,
    verificar_token_revogado,
)


logger = logging.getLogger(__name__)

auth_rota = APIRouter(tags=["Autenticação"])


# =========================================================
# CONFIGURAÇÕES DOS COOKIES
# =========================================================

TEMPO_ACCESS_TOKEN = settings.JWT_ACCESS_EXPIRE_MINUTES * 60
TEMPO_REFRESH_TOKEN = settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60


def configurar_cookies(
    resposta: JSONResponse,
    request: Request,
    access_token: str,
    refresh_token: str,
):
    cookie_seguro = request.url.scheme == "https"

    resposta.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=cookie_seguro,
        samesite="lax",
        max_age=TEMPO_ACCESS_TOKEN,
        path="/",
    )

    resposta.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=cookie_seguro,
        samesite="lax",
        max_age=TEMPO_REFRESH_TOKEN,
        path="/",
    )

    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"

    return resposta


def limpar_cookies(resposta: JSONResponse, request: Request):
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

    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"

    return resposta


def registrar_revogacao(payload: dict, db: Session):
    jti = payload["jti"]

    token_revogado = db.get(TokenRevogado, jti)

    if token_revogado is None:
        expira_em = datetime.fromtimestamp(
            payload["exp"],
            tz=timezone.utc,
        ).replace(tzinfo=None)

        db.add(
            TokenRevogado(
                jti=jti,
                expira_em=expira_em,
            )
        )


# =========================================================
# MODELO DE LOGIN
# =========================================================

class LoginRequest(BaseModel):
    usuario: EmailStr
    senha: str


# =========================================================
# LOGIN
# =========================================================

@auth_rota.post("/api/login")
def realizar_login(
    dados: LoginRequest,
    request: Request,
    db: Session = Depends(database.get_db),
):
    try:
        resultado = autenticar_usuario(
            db=db,
            email=str(dados.usuario),
            senha=dados.senha,
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(erro),
        ) from erro

    except RuntimeError as erro:
        logger.exception(
            "Erro durante a autenticação do usuário."
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o serviço de autenticação.",
        ) from erro

    perfil = resultado["usuario"]["perfil"]

    if perfil == "ADMINISTRADOR":
        url_destino = "/dashboard-admin"

    elif perfil == "OPERADOR":
        url_destino = "/dashboard-user"

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil de usuário não autorizado.",
        )

    resposta = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "mensagem": "Login realizado com sucesso.",
            "url": url_destino,
            "usuario": resultado["usuario"],
        },
    )

    return configurar_cookies(
        resposta,
        request,
        resultado["access_token"],
        resultado["refresh_token"],
    )


# =========================================================
# RENOVAÇÃO DA SESSÃO
# =========================================================

@auth_rota.post("/api/refresh")
def renovar_sessao(
    request: Request,
    db: Session = Depends(database.get_db),
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        resposta = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "autenticado": False,
                "mensagem": "Token de renovação não encontrado.",
            },
        )

        return limpar_cookies(resposta, request)

    try:
        # Valida assinatura, validade, emissor e tipo do token.
        payload = decodificar_token(
            refresh_token,
            tipo_esperado="refresh",
        )

        # Impede reutilização de um refresh token já revogado.
        if verificar_token_revogado(payload, db):
            raise ValueError("Token de renovação já utilizado ou revogado.")

        id_usuario = int(payload["sub"])

        usuario = db.get(User, id_usuario)

        if usuario is None or not usuario.ativo:
            raise ValueError("Usuário inexistente ou inativo.")

        # Revoga o refresh antigo antes de emitir outro.
        registrar_revogacao(payload, db)

        novo_access_token = criar_access_token(id_usuario)
        novo_refresh_token = criar_refresh_token(id_usuario)

        db.commit()

    except ValueError as erro:
        db.rollback()

        logger.warning(
            "Tentativa de renovação com token inválido: %s",
            erro,
        )

        resposta = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "autenticado": False,
                "mensagem": "Sessão expirada. Faça login novamente.",
            },
        )

        return limpar_cookies(resposta, request)

    except Exception:
        db.rollback()

        logger.exception(
            "Erro inesperado durante a renovação da sessão."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível renovar a sessão.",
        )

    resposta = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "autenticado": True,
            "mensagem": "Sessão renovada com sucesso.",
        },
    )

    return configurar_cookies(
        resposta,
        request,
        novo_access_token,
        novo_refresh_token,
    )


# =========================================================
# VERIFICAR SESSÃO
# =========================================================

@auth_rota.get("/api/verificar-sessao")
def verificar_sessao(
    request: Request,
    db: Session = Depends(database.get_db),
):
    from routes import user_rota

    autenticacao = user_rota.obter_usuario_autenticado(
        request,
        db,
    )

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida, expirada ou encerrada.",
        )

    return {
        "autenticado": True,
        "mensagem": "Sessão válida.",
    }


# =========================================================
# LOGOUT
# =========================================================

@auth_rota.post("/api/logout")
def realizar_logout(
    request: Request,
    db: Session = Depends(database.get_db),
):
    tokens = [
        ("access_token", "access"),
        ("refresh_token", "refresh"),
    ]

    try:
        for nome_cookie, tipo_token in tokens:
            token = request.cookies.get(nome_cookie)

            if not token:
                continue

            try:
                payload = decodificar_token(
                    token,
                    tipo_esperado=tipo_token,
                )

                registrar_revogacao(payload, db)

            except (
                ValueError,
                KeyError,
                TypeError,
                OSError,
            ):
                # Token inválido ou expirado.
                continue

        db.commit()

    except Exception as erro:
        db.rollback()

        logger.exception(
            "Erro ao encerrar a sessão do usuário."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível encerrar a sessão.",
        ) from erro

    resposta = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "mensagem": "Sessão encerrada com sucesso.",
            "url": "/",
        },
    )

    return limpar_cookies(resposta, request)