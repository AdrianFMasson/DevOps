
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field as PydanticField
from sqlmodel import Session
from db.db import database
from controller import VagasMensalistasController as controller

vagas_mensalistas_rota = APIRouter(
    prefix="/api/vagas-mensalistas",
    tags=["Vagas Mensalistas"]
)

class VinculoCriacao(BaseModel):
    id_clients: int = PydanticField(gt=0)
    id_vaga: int = PydanticField(gt=0)
    data_inicio: date
    data_fim: Optional[date] = None

class VinculoAtualizacao(BaseModel):
    id_clients: Optional[int] = PydanticField(default=None, gt=0)
    id_vaga: Optional[int] = PydanticField(default=None, gt=0)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None

class VinculoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_vinculo: int
    id_clients: int
    id_vaga: int
    data_inicio: date
    data_fim: Optional[date]
    dt_cadastro: Optional[datetime]

def obter_db():
    yield from database.get_db()

@vagas_mensalistas_rota.get("", response_model=list[VinculoResposta])
def listar_vinculos(
    incluir_encerrados: bool = Query(default=True),
    db: Session = Depends(obter_db)
):
    return controller.listar_vinculos(db, incluir_encerrados)

@vagas_mensalistas_rota.get("/{id_vinculo}", response_model=VinculoResposta)
def buscar_vinculo(
    id_vinculo: int,
    db: Session = Depends(obter_db)
):
    return controller.buscar_vinculo(db, id_vinculo)

@vagas_mensalistas_rota.post("", response_model=VinculoResposta, status_code=status.HTTP_201_CREATED)
def criar_vinculo(
    dados: VinculoCriacao,
    db: Session = Depends(obter_db)
):
    return controller.criar_vinculo(db, **dados.model_dump())

@vagas_mensalistas_rota.put("/{id_vinculo}", response_model=VinculoResposta)
def atualizar_vinculo(
    id_vinculo: int,
    dados: VinculoAtualizacao,
    db: Session = Depends(obter_db)
):
    dados_validos = dados.model_dump(exclude_unset=True)
    return controller.atualizar_vinculo(db, id_vinculo, dados_validos)

@vagas_mensalistas_rota.patch("/{id_vinculo}/encerrar", response_model=VinculoResposta)
def encerrar_vinculo(
    id_vinculo: int,
    data_fim: Optional[date] = Query(default=None),
    db: Session = Depends(obter_db)
):
    return controller.encerrar_vinculo(db, id_vinculo, data_fim)
