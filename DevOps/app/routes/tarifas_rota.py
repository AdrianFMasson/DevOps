
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field as PydanticField
from sqlmodel import Session
from db.db import database
from controller import TarifasController as controller

tarifas_rota = APIRouter(prefix="/api/tarifas", tags=["Tarifas"])

class TarifaCriacao(BaseModel):
    nome: str = PydanticField(min_length=1, max_length=100)
    valor_hora: Decimal = PydanticField(ge=0, max_digits=10, decimal_places=2)
    minutos_tolerancia: int = PydanticField(default=0, ge=0, le=65535)
    minutos_fracao: int = PydanticField(default=60, gt=0, le=65535)
    valor_fracao: Decimal = PydanticField(ge=0, max_digits=10, decimal_places=2)
    inicio_vigencia: datetime
    fim_vigencia: Optional[datetime] = None
    ativo: bool = True

class TarifaAtualizacao(BaseModel):
    nome: Optional[str] = PydanticField(default=None, min_length=1, max_length=100)
    valor_hora: Optional[Decimal] = PydanticField(default=None, ge=0, max_digits=10, decimal_places=2)
    minutos_tolerancia: Optional[int] = PydanticField(default=None, ge=0, le=65535)
    minutos_fracao: Optional[int] = PydanticField(default=None, gt=0, le=65535)
    valor_fracao: Optional[Decimal] = PydanticField(default=None, ge=0, max_digits=10, decimal_places=2)
    inicio_vigencia: Optional[datetime] = None
    fim_vigencia: Optional[datetime] = None
    ativo: Optional[bool] = None

class TarifaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_tarifa: int
    nome: str
    valor_hora: Decimal
    minutos_tolerancia: int
    minutos_fracao: int
    valor_fracao: Decimal
    inicio_vigencia: datetime
    fim_vigencia: Optional[datetime]
    ativo: bool
    dt_cadastro: Optional[datetime]

def obter_db():
    yield from database.get_db()

@tarifas_rota.get("", response_model=list[TarifaResposta])
def listar_tarifas(
    incluir_inativas: bool = Query(default=True),
    db: Session = Depends(obter_db)
):
    return controller.listar_tarifas(db, incluir_inativas)

@tarifas_rota.get("/{id_tarifa}", response_model=TarifaResposta)
def buscar_tarifa(id_tarifa: int, db: Session = Depends(obter_db)):
    return controller.buscar_tarifa(db, id_tarifa)

@tarifas_rota.post("", response_model=TarifaResposta, status_code=status.HTTP_201_CREATED)
def criar_tarifa(dados: TarifaCriacao, db: Session = Depends(obter_db)):
    return controller.criar_tarifa(db, dados.model_dump())

@tarifas_rota.put("/{id_tarifa}", response_model=TarifaResposta)
def atualizar_tarifa(id_tarifa: int, dados: TarifaAtualizacao, db: Session = Depends(obter_db)):
    return controller.atualizar_tarifa(db, id_tarifa, dados.model_dump(exclude_unset=True))

@tarifas_rota.patch("/{id_tarifa}/desativar", response_model=TarifaResposta)
def desativar_tarifa(id_tarifa: int, db: Session = Depends(obter_db)):
    return controller.desativar_tarifa(db, id_tarifa)
