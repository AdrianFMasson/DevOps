
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from config.Config import settings


_hasher = PasswordHash.recommended()


def criptografar_senha(senha: str) -> str:
    if not senha:
        raise ValueError("A senha não pode ser vazia.")

    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    if not senha or not senha_hash:
        return False

    try:
        return _hasher.verify(senha, senha_hash)
    except (ValueError, TypeError):
        return False


def _criar_token(
    id_usuario: int,
    tipo: str,
    duracao: timedelta,
) -> str:
    if not isinstance(id_usuario, int) or id_usuario <= 0:
        raise ValueError("Identificador de usuário inválido.")

    if tipo not in {"access", "refresh"}:
        raise ValueError("Tipo de token inválido.")

    agora = datetime.now(timezone.utc)

    payload = {
        "sub": str(id_usuario),
        "type": tipo,
        "iat": agora,
        "exp": agora + duracao,
        "iss": settings.JWT_ISSUER,
        "jti": str(uuid4()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def criar_access_token(id_usuario: int) -> str:
    return _criar_token(
        id_usuario=id_usuario,
        tipo="access",
        duracao=timedelta(
            minutes=settings.JWT_ACCESS_EXPIRE_MINUTES
        ),
    )


def criar_refresh_token(id_usuario: int) -> str:
    return _criar_token(
        id_usuario=id_usuario,
        tipo="refresh",
        duracao=timedelta(
            days=settings.JWT_REFRESH_EXPIRE_DAYS
        ),
    )


def decodificar_token(
    token: str,
    tipo_esperado: str = "access",
) -> dict:
    if not isinstance(token, str) or not token.strip():
        raise ValueError("Token ausente ou inválido.")

    if tipo_esperado not in {"access", "refresh"}:
        raise ValueError("Tipo de token esperado inválido.")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={
                "require": [
                    "sub",
                    "type",
                    "iat",
                    "exp",
                    "iss",
                    "jti",
                ],
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_iss": True,
            },
        )

    except jwt.ExpiredSignatureError as erro:
        raise ValueError("Token expirado.") from erro

    except jwt.InvalidTokenError as erro:
        raise ValueError("Token inválido ou expirado.") from erro

    if not isinstance(payload, dict):
        raise ValueError("Conteúdo do token inválido.")

    if payload.get("type") != tipo_esperado:
        raise ValueError("Tipo de token inválido.")

    id_usuario = payload.get("sub")

    if (
        not isinstance(id_usuario, str)
        or not id_usuario.isdigit()
        or int(id_usuario) <= 0
    ):
        raise ValueError("Identificador de usuário inválido.")

    if not isinstance(payload.get("jti"), str) or not payload["jti"]:
        raise ValueError("Identificador do token inválido.")

    return payload
