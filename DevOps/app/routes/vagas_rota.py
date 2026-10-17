
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import TipoVaga, StatusVaga
from controller.VagasController import listar_vagas, buscar_vaga, cadastrar_vaga, atualizar_vaga, excluir_vaga

vagas_rota = APIRouter(prefix="/api/vagas", tags=["Vagas"])

class VagaCriacao(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    tipo: TipoVaga
    status: StatusVaga = StatusVaga.ATIVA

class VagaAtualizacao(BaseModel):
    codigo: Optional[str] = Field(default=None, min_length=1, max_length=20)
    tipo: Optional[TipoVaga] = None
    status: Optional[StatusVaga] = None

class VagaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_vaga: int
    codigo: str
    tipo: TipoVaga
    status: StatusVaga
    dt_cadastro: Optional[str] = None
    dt_atualizacao: Optional[str] = None

@vagas_rota.get("", response_model=list[VagaResposta], status_code=status.HTTP_200_OK)
def obter_vagas(db: Session = Depends(database.get_db)):
    return listar_vagas(db)

@vagas_rota.get("/{id_vaga}", response_model=VagaResposta, status_code=status.HTTP_200_OK)
def obter_vaga(id_vaga: int, db: Session = Depends(database.get_db)):
    return buscar_vaga(db, id_vaga)

@vagas_rota.post("", response_model=VagaResposta, status_code=status.HTTP_201_CREATED)
def criar_vaga(dados: VagaCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_vaga(db, dados.model_dump())

@vagas_rota.put("/{id_vaga}", response_model=VagaResposta, status_code=status.HTTP_200_OK)
def editar_vaga(id_vaga: int, dados: VagaAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe pelo menos um campo para atualizar.")
    return atualizar_vaga(db, id_vaga, dados_atualizados)

@vagas_rota.delete("/{id_vaga}", response_model=VagaResposta, status_code=status.HTTP_200_OK)
def remover_vaga(id_vaga: int, db: Session = Depends(database.get_db)):
    return excluir_vaga(db, id_vaga)
