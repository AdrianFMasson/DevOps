
from datetime import date, datetime
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import VagaMensalista, Client, Vaga, TipoVaga, StatusVaga

def listar_vinculos(db: Session, incluir_encerrados: bool = True):
    consulta = select(VagaMensalista)
    if not incluir_encerrados:
        consulta = consulta.where(VagaMensalista.data_fim.is_(None))
    return db.exec(consulta.order_by(VagaMensalista.id_vinculo.desc())).all()

def buscar_vinculo(db: Session, id_vinculo: int):
    vinculo = db.get(VagaMensalista, id_vinculo)
    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo de mensalista não encontrado.")
    return vinculo

def validar_dados(db: Session, id_clients: int, id_vaga: int, data_inicio: date, data_fim: date | None, id_vinculo: int | None = None):
    cliente = db.get(Client, id_clients)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    if not cliente.ativo:
        raise HTTPException(status_code=400, detail="Não é possível vincular um cliente inativo.")

    vaga = db.get(Vaga, id_vaga)
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    if vaga.tipo != TipoVaga.MENSALISTA:
        raise HTTPException(status_code=400, detail="Somente vagas do tipo MENSALISTA podem receber vínculos.")
    if vaga.status != StatusVaga.ATIVA:
        raise HTTPException(status_code=400, detail="A vaga precisa estar ativa para receber um vínculo.")
    if data_fim is not None and data_fim < data_inicio:
        raise HTTPException(status_code=400, detail="A data final não pode ser anterior à data inicial.")

    if data_fim is None:
        consulta = select(VagaMensalista).where(
            VagaMensalista.id_vaga == id_vaga,
            VagaMensalista.data_fim.is_(None)
        )
        if id_vinculo is not None:
            consulta = consulta.where(VagaMensalista.id_vinculo != id_vinculo)
        if db.exec(consulta).first():
            raise HTTPException(status_code=409, detail="Esta vaga já possui um vínculo mensalista ativo.")

def criar_vinculo(db: Session, id_clients: int, id_vaga: int, data_inicio: date, data_fim: date | None = None):
    validar_dados(db, id_clients, id_vaga, data_inicio, data_fim)
    vinculo = VagaMensalista(
        id_clients=id_clients,
        id_vaga=id_vaga,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    try:
        db.add(vinculo)
        db.commit()
        db.refresh(vinculo)
        return vinculo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível criar o vínculo. Verifique se a vaga já possui um vínculo ativo.")

def atualizar_vinculo(db: Session, id_vinculo: int, dados: dict):
    vinculo = buscar_vinculo(db, id_vinculo)
    if vinculo.data_fim is not None:
        raise HTTPException(status_code=400, detail="Vínculos encerrados não podem ser alterados.")

    id_clients = dados.get("id_clients", vinculo.id_clients)
    id_vaga = dados.get("id_vaga", vinculo.id_vaga)
    data_inicio = dados.get("data_inicio", vinculo.data_inicio)
    data_fim = dados.get("data_fim", vinculo.data_fim)

    validar_dados(db, id_clients, id_vaga, data_inicio, data_fim, id_vinculo)

    for campo, valor in dados.items():
        if campo in {"id_clients", "id_vaga", "data_inicio", "data_fim"}:
            setattr(vinculo, campo, valor)

    try:
        db.add(vinculo)
        db.commit()
        db.refresh(vinculo)
        return vinculo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível atualizar o vínculo. Verifique os dados informados.")

def encerrar_vinculo(db: Session, id_vinculo: int, data_fim: date | None = None):
    vinculo = buscar_vinculo(db, id_vinculo)
    if vinculo.data_fim is not None:
        raise HTTPException(status_code=400, detail="Este vínculo já está encerrado.")

    data_encerramento = data_fim or date.today()
    if data_encerramento < vinculo.data_inicio:
        raise HTTPException(status_code=400, detail="A data de encerramento não pode ser anterior à data inicial.")

    vinculo.data_fim = data_encerramento
    try:
        db.add(vinculo)
        db.commit()
        db.refresh(vinculo)
        return vinculo
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível encerrar o vínculo.")
