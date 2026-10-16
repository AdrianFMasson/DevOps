
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select

from entities.models import User
from utils.seguranca import (
    verificar_senha,
    criar_access_token,
    criar_refresh_token
)


def autenticar_usuario(db: Session, email: str, senha: str) -> dict:
    email_normalizado = email.strip().lower()

    try:
        consulta = select(User).where(User.email == email_normalizado)
        usuario = db.exec(consulta).first()

        if usuario is None:
            raise ValueError("E-mail ou senha inválidos.")

        if not usuario.ativo:
            raise ValueError("Esta conta está desativada.")

        if not verificar_senha(senha, usuario.senha_hash):
            raise ValueError("E-mail ou senha inválidos.")

        id_usuario = usuario.id_usuario

        return {
            "mensagem": "Autenticação realizada com sucesso.",
            "usuario": {
                "id_usuario": id_usuario,
                "nome": usuario.nome,
                "email": usuario.email,
                "perfil": usuario.perfil.value,
                "ativo": usuario.ativo
            },
            "access_token": criar_access_token(id_usuario),
            "refresh_token": criar_refresh_token(id_usuario),
            "token_type": "bearer"
        }

    except OperationalError as erro:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from erro
