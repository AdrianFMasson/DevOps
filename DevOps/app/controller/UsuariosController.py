
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from entities.models import User


def listar_usuarios(db: Session):
    return db.exec(
        select(User).order_by(User.id_usuario.desc())
    ).all()


def buscar_usuario(db: Session, id_usuario: int):
    usuario = db.get(User, id_usuario)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )
    return usuario


def cadastrar_usuario(db: Session, dados: dict):
    usuario_existente = db.exec(
        select(User).where(User.email == dados["email"])
    ).first()

    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário cadastrado com este e-mail."
        )

    usuario = User(**dados)
    db.add(usuario)

    try:
        db.commit()
        db.refresh(usuario)
        return usuario
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível cadastrar o usuário devido a um conflito de dados."
        )


def atualizar_usuario(db: Session, id_usuario: int, dados: dict):
    usuario = buscar_usuario(db, id_usuario)

    if "email" in dados and dados["email"] != usuario.email:
        email_existente = db.exec(
            select(User).where(User.email == dados["email"])
        ).first()

        if email_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe um usuário cadastrado com este e-mail."
            )

    for campo, valor in dados.items():
        setattr(usuario, campo, valor)

    try:
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível atualizar o usuário devido a um conflito de dados."
        )


def desativar_usuario(db: Session, id_usuario: int):
    usuario = buscar_usuario(db, id_usuario)

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O usuário já está desativado."
        )

    usuario.ativo = False
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
