
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import Tarifa

def listar_tarifas(db: Session, incluir_inativas: bool = True):
    consulta = select(Tarifa)
    if not incluir_inativas:
        consulta = consulta.where(Tarifa.ativo.is_(True))
    return db.exec(consulta.order_by(Tarifa.id_tarifa.desc())).all()

def buscar_tarifa(db: Session, id_tarifa: int):
    tarifa = db.get(Tarifa, id_tarifa)
    if not tarifa:
        raise HTTPException(status_code=404, detail="Tarifa não encontrada.")
    return tarifa

def validar_dados(dados: dict, tarifa_atual: Tarifa | None = None):
    nome = dados.get("nome", tarifa_atual.nome if tarifa_atual else "")
    valor_hora = dados.get("valor_hora", tarifa_atual.valor_hora if tarifa_atual else Decimal("0"))
    minutos_tolerancia = dados.get("minutos_tolerancia", tarifa_atual.minutos_tolerancia if tarifa_atual else 0)
    minutos_fracao = dados.get("minutos_fracao", tarifa_atual.minutos_fracao if tarifa_atual else 60)
    valor_fracao = dados.get("valor_fracao", tarifa_atual.valor_fracao if tarifa_atual else Decimal("0"))
    inicio_vigencia = dados.get("inicio_vigencia", tarifa_atual.inicio_vigencia if tarifa_atual else None)
    fim_vigencia = dados.get("fim_vigencia", tarifa_atual.fim_vigencia if tarifa_atual else None)

    if not nome or not nome.strip():
        raise HTTPException(status_code=400, detail="O nome da tarifa é obrigatório.")
    if valor_hora < 0 or valor_fracao < 0:
        raise HTTPException(status_code=400, detail="Os valores da tarifa não podem ser negativos.")
    if minutos_tolerancia < 0:
        raise HTTPException(status_code=400, detail="A tolerância não pode ser negativa.")
    if minutos_fracao <= 0:
        raise HTTPException(status_code=400, detail="Os minutos por fração devem ser maiores que zero.")
    if inicio_vigencia is None:
        raise HTTPException(status_code=400, detail="A data inicial da vigência é obrigatória.")
    if fim_vigencia is not None and fim_vigencia <= inicio_vigencia:
        raise HTTPException(status_code=400, detail="O fim da vigência deve ser posterior ao início.")

def criar_tarifa(db: Session, dados: dict):
    validar_dados(dados)
    dados["nome"] = dados["nome"].strip()
    tarifa = Tarifa(**dados)
    try:
        db.add(tarifa)
        db.commit()
        db.refresh(tarifa)
        return tarifa
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível cadastrar a tarifa. Verifique os dados.")

def atualizar_tarifa(db: Session, id_tarifa: int, dados: dict):
    tarifa = buscar_tarifa(db, id_tarifa)
    validar_dados(dados, tarifa)
    if "nome" in dados:
        dados["nome"] = dados["nome"].strip()
    for campo, valor in dados.items():
        setattr(tarifa, campo, valor)
    try:
        db.add(tarifa)
        db.commit()
        db.refresh(tarifa)
        return tarifa
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível atualizar a tarifa.")

def desativar_tarifa(db: Session, id_tarifa: int):
    tarifa = buscar_tarifa(db, id_tarifa)
    if not tarifa.ativo:
        raise HTTPException(status_code=400, detail="Esta tarifa já está inativa.")
    tarifa.ativo = False
    try:
        db.add(tarifa)
        db.commit()
        db.refresh(tarifa)
        return tarifa
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível desativar a tarifa.")
