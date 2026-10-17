
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import Vaga, VagaMensalista

def listar_vagas(db: Session):
    return db.exec(select(Vaga).order_by(Vaga.id_vaga.desc())).all()

def buscar_vaga(db: Session, id_vaga: int):
    vaga = db.get(Vaga, id_vaga)
    if vaga is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada.")
    return vaga

def cadastrar_vaga(db: Session, dados: dict):
    codigo = dados["codigo"].strip().upper()
    existente = db.exec(select(Vaga).where(Vaga.codigo == codigo)).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma vaga com esse código.")
    dados["codigo"] = codigo
    vaga = Vaga(**dados)
    db.add(vaga)
    try:
        db.commit()
        db.refresh(vaga)
        return vaga
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível cadastrar a vaga. Verifique o código e os dados informados.")

def atualizar_vaga(db: Session, id_vaga: int, dados: dict):
    vaga = buscar_vaga(db, id_vaga)
    if "codigo" in dados:
        dados["codigo"] = dados["codigo"].strip().upper()
        existente = db.exec(select(Vaga).where(Vaga.codigo == dados["codigo"], Vaga.id_vaga != id_vaga)).first()
        if existente:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esse código já pertence a outra vaga.")
    for campo, valor in dados.items():
        setattr(vaga, campo, valor)
    db.add(vaga)
    try:
        db.commit()
        db.refresh(vaga)
        return vaga
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível atualizar a vaga.")

def excluir_vaga(db: Session, id_vaga: int):
    vaga = buscar_vaga(db, id_vaga)
    vinculo_ativo = db.exec(select(VagaMensalista).where(VagaMensalista.id_vaga == id_vaga, VagaMensalista.data_fim.is_(None))).first()
    if vinculo_ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A vaga possui um vínculo mensalista ativo e não pode ser desativada.")
    vaga.status = "INATIVA"
    db.add(vaga)
    try:
        db.commit()
        db.refresh(vaga)
        return vaga
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não foi possível desativar a vaga.")
