
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import Client, ModeloVeiculo, Veiculo

def listar_veiculos(db: Session):
    return db.exec(select(Veiculo).order_by(Veiculo.id_veiculo.desc())).all()

def buscar_veiculo(db: Session, id_veiculo: int):
    veiculo = db.get(Veiculo, id_veiculo)
    if veiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")
    return veiculo

def validar_relacionamentos(db: Session, id_clients: int, id_modelo: int):
    cliente = db.get(Client, id_clients)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
    if not cliente.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é possível associar um veículo a um cliente desativado.")
    modelo = db.get(ModeloVeiculo, id_modelo)
    if modelo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo de veículo não encontrado.")
    if not modelo.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é possível associar um veículo a um modelo desativado.")

def cadastrar_veiculo(db: Session, dados: dict):
    validar_relacionamentos(db, dados["id_clients"], dados["id_modelo"])
    placa = dados["placa"].strip().upper()
    existente = db.exec(select(Veiculo).where(Veiculo.placa == placa)).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um veículo cadastrado com essa placa.")
    dados["placa"] = placa
    veiculo = Veiculo(**dados)
    db.add(veiculo)
    try:
        db.commit()
        db.refresh(veiculo)
        return veiculo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível cadastrar o veículo. Verifique a placa, o cliente, o modelo e os dados informados.")

def atualizar_veiculo(db: Session, id_veiculo: int, dados: dict):
    veiculo = buscar_veiculo(db, id_veiculo)
    id_clients = dados.get("id_clients", veiculo.id_clients)
    id_modelo = dados.get("id_modelo", veiculo.id_modelo)
    validar_relacionamentos(db, id_clients, id_modelo)
    if "placa" in dados:
        dados["placa"] = dados["placa"].strip().upper()
        existente = db.exec(select(Veiculo).where(Veiculo.placa == dados["placa"], Veiculo.id_veiculo != id_veiculo)).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Essa placa já pertence a outro veículo.")
    for campo, valor in dados.items():
        setattr(veiculo, campo, valor)
    db.add(veiculo)
    try:
        db.commit()
        db.refresh(veiculo)
        return veiculo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível atualizar o veículo. Verifique os dados informados.")

def desativar_veiculo(db: Session, id_veiculo: int):
    veiculo = buscar_veiculo(db, id_veiculo)
    if not veiculo.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esse veículo já está desativado.")
    veiculo.ativo = False
    db.add(veiculo)
    try:
        db.commit()
        db.refresh(veiculo)
        return veiculo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível desativar o veículo.")
