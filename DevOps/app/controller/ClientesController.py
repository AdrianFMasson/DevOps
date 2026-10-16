
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import Client

def listar_clientes(db: Session):
    return db.exec(select(Client).order_by(Client.id_clients.desc())).all()

def buscar_cliente(db: Session, id_clients: int):
    cliente = db.get(Client, id_clients)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    return cliente

def cadastrar_cliente(db: Session, dados: dict):
    documento = dados.get("documento")
    if documento:
        existente = db.exec(select(Client).where(Client.documento == documento)).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um cliente com esse documento.")
    cliente = Client(**dados)
    db.add(cliente)
    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível cadastrar o cliente. Verifique se o documento já está cadastrado e se os dados são válidos.")

def atualizar_cliente(db: Session, id_clients: int, dados: dict):
    cliente = buscar_cliente(db, id_clients)
    documento = dados.get("documento")
    if documento:
        existente = db.exec(select(Client).where(Client.documento == documento, Client.id_clients != id_clients)).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esse documento já pertence a outro cliente.")
    for campo, valor in dados.items():
        setattr(cliente, campo, valor)
    db.add(cliente)
    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível atualizar o cliente. Verifique os dados informados.")

def desativar_cliente(db: Session, id_clients: int):
    cliente = buscar_cliente(db, id_clients)
    if not cliente.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esse cliente já está desativado.")
    cliente.ativo = False
    db.add(cliente)
    try:
        db.commit()
        db.refresh(cliente)
        return cliente
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível desativar o cliente.")
