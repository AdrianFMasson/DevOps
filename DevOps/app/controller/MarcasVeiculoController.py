
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import MarcaVeiculo, ModeloVeiculo

def listar_marcas(db: Session):
    return db.exec(select(MarcaVeiculo).order_by(MarcaVeiculo.id_marca.desc())).all()

def buscar_marca(db: Session, id_marca: int):
    marca = db.get(MarcaVeiculo, id_marca)
    if marca is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca não encontrada.")
    return marca

def cadastrar_marca(db: Session, dados: dict):
    existente = db.exec(select(MarcaVeiculo).where(MarcaVeiculo.nome == dados["nome"])).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma marca com esse nome.")
    marca = MarcaVeiculo(**dados)
    db.add(marca)
    try:
        db.commit()
        db.refresh(marca)
        return marca
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível cadastrar a marca. Verifique se o nome já está cadastrado.")

def atualizar_marca(db: Session, id_marca: int, dados: dict):
    marca = buscar_marca(db, id_marca)
    if "nome" in dados:
        existente = db.exec(select(MarcaVeiculo).where(MarcaVeiculo.nome == dados["nome"], MarcaVeiculo.id_marca != id_marca)).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe outra marca com esse nome.")
    for campo, valor in dados.items():
        setattr(marca, campo, valor)
    db.add(marca)
    try:
        db.commit()
        db.refresh(marca)
        return marca
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível atualizar a marca.")

def desativar_marca(db: Session, id_marca: int):
    marca = buscar_marca(db, id_marca)
    if not marca.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Essa marca já está desativada.")
    modelos_ativos = db.exec(select(ModeloVeiculo).where(ModeloVeiculo.id_marca == id_marca, ModeloVeiculo.ativo == True)).first()
    if modelos_ativos:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A marca possui modelos ativos. Desative os modelos antes de desativar a marca.")
    marca.ativo = False
    db.add(marca)
    try:
        db.commit()
        db.refresh(marca)
        return marca
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível desativar a marca.")
