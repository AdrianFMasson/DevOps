from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlmodel import Session

from db.db import database
from controller.AuthController import autenticar_usuario
from entities.models import TokenRevogado
from utils.seguranca import decodificar_token


auth_rota = APIRouter(tags=["Autenticação"])


# =========================================================
# MODELO DE LOGIN
# =========================================================

class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario: EmailStr
    senha: str


# =========================================================
# LOGIN
# =========================================================

@auth_rota.post("/api/login")
def realizar_login(
    dados: LoginRequest,
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

    resposta.set_cookie(
        key="access_token",
        value=resultado["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60,
        path="/",
    )

    resposta.set_cookie(
        key="refresh_token",
        value=resultado["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"

    return resposta


# =========================================================
# VERIFICAR SESSÃO
# =========================================================

@auth_rota.get("/api/verificar-sessao")
def verificar_sessao(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Verifica no servidor se o access_token continua válido.

    Reutiliza a validação central existente em user_rota.py,
    incluindo a consulta de tokens revogados.
    """

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

                jti = payload["jti"]

                expira_em = datetime.fromtimestamp(
                    payload["exp"],
                    tz=timezone.utc,
                ).replace(tzinfo=None)

                token_revogado = db.get(
                    TokenRevogado,
                    jti,
                )

                if token_revogado is None:
                    db.add(
                        TokenRevogado(
                            jti=jti,
                            expira_em=expira_em,
                        )
                    )

            except (
                ValueError,
                KeyError,
                TypeError,
                OSError,
            ):
                # Token inválido ou expirado.
                # Não pode ser utilizado para autenticar.
                continue

        db.commit()

    except Exception as erro:
        db.rollback()

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

    resposta.delete_cookie(
        key="access_token",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )

    resposta.delete_cookie(
        key="refresh_token",
        path="/",
        secure=False,
        httponly=True,
        samesite="lax",
    )

    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"

    return resposta