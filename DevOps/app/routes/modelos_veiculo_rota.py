
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import ModeloVeiculo
from controller.ModelosVeiculoController import listar_modelos, buscar_modelo, cadastrar_modelo, atualizar_modelo, desativar_modelo

modelos_veiculo_rota = APIRouter(prefix="/api/modelos-veiculo", tags=["Modelos de veículos"])

class ModeloCriacao(BaseModel):
    id_marca: int = Field(gt=0)
    nome: str = Field(min_length=1, max_length=100)

class ModeloAtualizacao(BaseModel):
    id_marca: Optional[int] = Field(default=None, gt=0)
    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    ativo: Optional[bool] = None

class ModeloResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_modelo: int
    id_marca: int
    nome: str
    ativo: bool
    dt_cadastro: Optional[str] = None
    dt_atualizacao: Optional[str] = None

@modelos_veiculo_rota.get("", response_model=list[ModeloResposta], status_code=status.HTTP_200_OK)
def obter_modelos(db: Session = Depends(database.get_db)):
    return listar_modelos(db)

@modelos_veiculo_rota.get("/{id_modelo}", response_model=ModeloResposta, status_code=status.HTTP_200_OK)
def obter_modelo(id_modelo: int, db: Session = Depends(database.get_db)):
    return buscar_modelo(db, id_modelo)

@modelos_veiculo_rota.post("", response_model=ModeloResposta, status_code=status.HTTP_201_CREATED)
def criar_modelo(dados: ModeloCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_modelo(db, dados.model_dump())

@modelos_veiculo_rota.put("/{id_modelo}", response_model=ModeloResposta, status_code=status.HTTP_200_OK)
def editar_modelo(id_modelo: int, dados: ModeloAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe pelo menos um campo para atualizar.")
    return atualizar_modelo(db, id_modelo, dados_atualizados)

@modelos_veiculo_rota.delete("/{id_modelo}", status_code=status.HTTP_200_OK)
def remover_modelo(id_modelo: int, db: Session = Depends(database.get_db)):
    modelo = desativar_modelo(db, id_modelo)
    return {"mensagem": "Modelo desativado com sucesso.", "id_modelo": modelo.id_modelo, "ativo": modelo.ativo}
