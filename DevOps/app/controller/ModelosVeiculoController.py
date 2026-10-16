
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import MarcaVeiculo, ModeloVeiculo, Veiculo

def listar_modelos(db: Session):
    return db.exec(select(ModeloVeiculo).order_by(ModeloVeiculo.id_modelo.desc())).all()

def buscar_modelo(db: Session, id_modelo: int):
    modelo = db.get(ModeloVeiculo, id_modelo)
    if modelo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo não encontrado.")
    return modelo

def cadastrar_modelo(db: Session, dados: dict):
    marca = db.get(MarcaVeiculo, dados["id_marca"])
    if marca is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca não encontrada.")
    if not marca.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é possível cadastrar um modelo para uma marca desativada.")
    existente = db.exec(select(ModeloVeiculo).where(ModeloVeiculo.id_marca == dados["id_marca"], ModeloVeiculo.nome == dados["nome"])).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esse modelo já está cadastrado para essa marca.")
    modelo = ModeloVeiculo(**dados)
    db.add(modelo)
    try:
        db.commit()
        db.refresh(modelo)
        return modelo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível cadastrar o modelo. Verifique a marca e os dados informados.")

def atualizar_modelo(db: Session, id_modelo: int, dados: dict):
    modelo = buscar_modelo(db, id_modelo)
    id_marca = dados.get("id_marca", modelo.id_marca)
    nome = dados.get("nome", modelo.nome)
    marca = db.get(MarcaVeiculo, id_marca)
    if marca is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca não encontrada.")
    if not marca.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não é possível associar o modelo a uma marca desativada.")
    existente = db.exec(select(ModeloVeiculo).where(ModeloVeiculo.id_marca == id_marca, ModeloVeiculo.nome == nome, ModeloVeiculo.id_modelo != id_modelo)).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe esse modelo cadastrado para a marca selecionada.")
    if dados.get("ativo") is True and not modelo.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A reativação de modelos desativados deve ser tratada separadamente.")
    for campo, valor in dados.items():
        setattr(modelo, campo, valor)
    db.add(modelo)
    try:
        db.commit()
        db.refresh(modelo)
        return modelo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível atualizar o modelo. Verifique os dados informados.")

def desativar_modelo(db: Session, id_modelo: int):
    modelo = buscar_modelo(db, id_modelo)
    if not modelo.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esse modelo já está desativado.")
    veiculo_ativo = db.exec(select(Veiculo).where(Veiculo.id_modelo == id_modelo, Veiculo.ativo == True)).first()
    if veiculo_ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Existem veículos ativos vinculados a esse modelo. Desative os veículos antes.")
    modelo.ativo = False
    db.add(modelo)
    try:
        db.commit()
        db.refresh(modelo)
        return modelo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível desativar o modelo.")
