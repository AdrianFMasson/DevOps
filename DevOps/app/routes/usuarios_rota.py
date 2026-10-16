
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlmodel import Session

from db.db import database
from entities.models import PerfilUsuario, User
from controller.UsuariosController import (
    listar_usuarios,
    buscar_usuario,
    cadastrar_usuario,
    atualizar_usuario,
    desativar_usuario,
)

usuarios_rota = APIRouter(
    prefix="/api/usuarios",
    tags=["Usuários"]
)


class UsuarioCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha_hash: str = Field(min_length=1, max_length=255)
    perfil: PerfilUsuario = PerfilUsuario.OPERADOR


class UsuarioAtualizacao(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None
    senha_hash: Optional[str] = Field(default=None, min_length=1, max_length=255)
    perfil: Optional[PerfilUsuario] = None
    ativo: Optional[bool] = None


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nome: str
    email: str
    perfil: PerfilUsuario
    ativo: bool


@usuarios_rota.get(
    "",
    response_model=list[UsuarioResposta],
    status_code=status.HTTP_200_OK
)
def obter_usuarios(
    db: Session = Depends(database.get_db)
):
    return listar_usuarios(db)


@usuarios_rota.get(
    "/{id_usuario}",
    response_model=UsuarioResposta,
    status_code=status.HTTP_200_OK
)
def obter_usuario(
    id_usuario: int,
    db: Session = Depends(database.get_db)
):
    return buscar_usuario(db, id_usuario)


@usuarios_rota.post(
    "",
    response_model=UsuarioResposta,
    status_code=status.HTTP_201_CREATED
)
def criar_usuario(
    dados: UsuarioCriacao,
    db: Session = Depends(database.get_db)
):
    return cadastrar_usuario(
        db,
        dados.model_dump()
    )


@usuarios_rota.put(
    "/{id_usuario}",
    response_model=UsuarioResposta,
    status_code=status.HTTP_200_OK
)
def editar_usuario(
    id_usuario: int,
    dados: UsuarioAtualizacao,
    db: Session = Depends(database.get_db)
):
    dados_atualizados = dados.model_dump(exclude_unset=True)

    if not dados_atualizados:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe ao menos um campo para atualizar."
        )

    return atualizar_usuario(
        db,
        id_usuario,
        dados_atualizados
    )


@usuarios_rota.delete(
    "/{id_usuario}",
    status_code=status.HTTP_200_OK
)
def excluir_usuario(
    id_usuario: int,
    db: Session = Depends(database.get_db)
):
    usuario = desativar_usuario(db, id_usuario)

    return {
        "mensagem": "Usuário desativado com sucesso.",
        "id_usuario": usuario.id_usuario,
        "ativo": usuario.ativo
    }
