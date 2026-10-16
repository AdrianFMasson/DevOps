
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


def _criar_token(id_usuario: int, tipo: str, duracao: timedelta) -> str:
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": str(id_usuario),
        "type": tipo,
        "iat": agora,
        "exp": agora + duracao,
        "iss": settings.JWT_ISSUER,
        "jti": str(uuid4())
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def criar_access_token(id_usuario: int) -> str:
    return _criar_token(
        id_usuario,
        "access",
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    )


def criar_refresh_token(id_usuario: int) -> str:
    return _criar_token(
        id_usuario,
        "refresh",
        timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )


def decodificar_token(token: str, tipo_esperado: str = "access") -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"require": ["sub", "type", "iat", "exp", "iss", "jti"]}
        )

        if payload.get("type") != tipo_esperado:
            raise ValueError("Tipo de token inválido.")

        if not payload["sub"].isdigit():
            raise ValueError("Identificador de usuário inválido.")

        return payload

    except jwt.ExpiredSignatureError as erro:
        raise ValueError("Token expirado.") from erro
    except jwt.InvalidTokenError as erro:
        raise ValueError("Token inválido.") from erro
