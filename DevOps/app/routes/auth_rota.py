
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlmodel import Session

from db.db import database
from controller.AuthController import autenticar_usuario


auth_rota = APIRouter(tags=["Autenticação"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario: EmailStr
    senha: str


@auth_rota.post("/api/login")
def realizar_login(
    dados: LoginRequest,
    db: Session = Depends(database.get_db)
):
    try:
        resultado = autenticar_usuario(
            db=db,
            email=str(dados.usuario),
            senha=dados.senha
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(erro)
        ) from erro

    except RuntimeError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível acessar o serviço de autenticação."
        ) from erro

    perfil = resultado["usuario"]["perfil"]

    if perfil == "ADMINISTRADOR":
        url_destino = "/dashboard-admin"
    elif perfil == "OPERADOR":
        url_destino = "/dashboard-user"
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil de usuário não autorizado."
        )

    resposta = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "mensagem": "Login realizado com sucesso.",
            "url": url_destino,
            "usuario": resultado["usuario"]
        }
    )

    resposta.set_cookie(
        key="access_token",
        value=resultado["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60,
        path="/"
    )

    resposta.set_cookie(
        key="refresh_token",
        value=resultado["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )

    resposta.headers["Cache-Control"] = "no-store"
    resposta.headers["Pragma"] = "no-cache"

    return resposta
