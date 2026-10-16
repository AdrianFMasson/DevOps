
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import Client, TelefoneClient

def listar_telefones(db: Session):
    return db.exec(select(TelefoneClient).order_by(TelefoneClient.id_telefone.desc())).all()

def buscar_telefone(db: Session, id_telefone: int):
    telefone = db.get(TelefoneClient, id_telefone)
    if telefone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telefone não encontrado.")
    return telefone

def cadastrar_telefone(db: Session, dados: dict):
    cliente = db.get(Client, dados["id_clients"])
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    if not cliente.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é possível adicionar telefone a um cliente desativado.")
    telefone = TelefoneClient(**dados)
    db.add(telefone)
    try:
        db.commit()
        db.refresh(telefone)
        return telefone
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível cadastrar o telefone. Verifique os dados e se o cliente já possui um telefone principal.")

def atualizar_telefone(db: Session, id_telefone: int, dados: dict):
    telefone = buscar_telefone(db, id_telefone)
    if "id_clients" in dados:
        cliente = db.get(Client, dados["id_clients"])
        if cliente is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
        if not cliente.ativo:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é possível associar o telefone a um cliente desativado.")
    for campo, valor in dados.items():
        setattr(telefone, campo, valor)
    db.add(telefone)
    try:
        db.commit()
        db.refresh(telefone)
        return telefone
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível atualizar o telefone. Verifique os dados e a regra de telefone principal.")

def excluir_telefone(db: Session, id_telefone: int):
    telefone = buscar_telefone(db, id_telefone)
    try:
        db.delete(telefone)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível excluir o telefone.")
