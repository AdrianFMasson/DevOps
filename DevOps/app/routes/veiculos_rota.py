
from typing import Optional
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import CorVeiculo
from controller.VeiculosController import listar_veiculos, buscar_veiculo, cadastrar_veiculo, atualizar_veiculo, desativar_veiculo

veiculos_rota = APIRouter(prefix="/api/veiculos", tags=["Veículos"])

class VeiculoCriacao(BaseModel):
    id_clients: int = Field(gt=0)
    id_modelo: int = Field(gt=0)
    placa: str = Field(min_length=7, max_length=7, pattern=r"^[A-Za-z]{3}[0-9][A-Za-z0-9][0-9]{2}$|^[A-Za-z]{3}[0-9]{4}$")
    cor: CorVeiculo = CorVeiculo.OUTRA
    ano_modelo: Optional[int] = Field(default=None, ge=1886, le=2100)

class VeiculoAtualizacao(BaseModel):
    id_clients: Optional[int] = Field(default=None, gt=0)
    id_modelo: Optional[int] = Field(default=None, gt=0)
    placa: Optional[str] = Field(default=None, min_length=7, max_length=7, pattern=r"^[A-Za-z]{3}[0-9][A-Za-z0-9][0-9]{2}$|^[A-Za-z]{3}[0-9]{4}$")
    cor: Optional[CorVeiculo] = None
    ano_modelo: Optional[int] = Field(default=None, ge=1886, le=2100)
    ativo: Optional[bool] = None

class VeiculoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_veiculo: int
    id_clients: int
    id_modelo: int
    placa: str
    cor: CorVeiculo
    ano_modelo: Optional[int]
    ativo: bool
    dt_cadastro: Optional[datetime] = None
    dt_atualizacao: Optional[datetime] = None

@veiculos_rota.get("", response_model=list[VeiculoResposta], status_code=status.HTTP_200_OK)
def obter_veiculos(db: Session = Depends(database.get_db)):
    return listar_veiculos(db)

@veiculos_rota.get("/{id_veiculo}", response_model=VeiculoResposta, status_code=status.HTTP_200_OK)
def obter_veiculo(id_veiculo: int, db: Session = Depends(database.get_db)):
    return buscar_veiculo(db, id_veiculo)

@veiculos_rota.post("", response_model=VeiculoResposta, status_code=status.HTTP_201_CREATED)
def criar_veiculo(dados: VeiculoCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_veiculo(db, dados.model_dump())

@veiculos_rota.put("/{id_veiculo}", response_model=VeiculoResposta, status_code=status.HTTP_200_OK)
def editar_veiculo(id_veiculo: int, dados: VeiculoAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe pelo menos um campo para atualizar.")
    return atualizar_veiculo(db, id_veiculo, dados_atualizados)

@veiculos_rota.delete("/{id_veiculo}", status_code=status.HTTP_200_OK)
def remover_veiculo(id_veiculo: int, db: Session = Depends(database.get_db)):
    veiculo = desativar_veiculo(db, id_veiculo)
    return {"mensagem": "Veículo desativado com sucesso.", "id_veiculo": veiculo.id_veiculo, "ativo": veiculo.ativo}
