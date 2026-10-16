
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import MarcaVeiculo
from controller.MarcasVeiculoController import listar_marcas, buscar_marca, cadastrar_marca, atualizar_marca, desativar_marca

marcas_veiculo_rota = APIRouter(prefix="/api/marcas-veiculo", tags=["Marcas de veículos"])

class MarcaCriacao(BaseModel):
    nome: str = Field(min_length=1, max_length=80)

class MarcaAtualizacao(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=80)
    ativo: Optional[bool] = None

class MarcaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_marca: int
    nome: str
    ativo: bool
    dt_cadastro: Optional[str] = None
    dt_atualizacao: Optional[str] = None

@marcas_veiculo_rota.get("", response_model=list[MarcaResposta], status_code=status.HTTP_200_OK)
def obter_marcas(db: Session = Depends(database.get_db)):
    return listar_marcas(db)

@marcas_veiculo_rota.get("/{id_marca}", response_model=MarcaResposta, status_code=status.HTTP_200_OK)
def obter_marca(id_marca: int, db: Session = Depends(database.get_db)):
    return buscar_marca(db, id_marca)

@marcas_veiculo_rota.post("", response_model=MarcaResposta, status_code=status.HTTP_201_CREATED)
def criar_marca(dados: MarcaCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_marca(db, dados.model_dump())

@marcas_veiculo_rota.put("/{id_marca}", response_model=MarcaResposta, status_code=status.HTTP_200_OK)
def editar_marca(id_marca: int, dados: MarcaAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe pelo menos um campo para atualizar.")
    return atualizar_marca(db, id_marca, dados_atualizados)

@marcas_veiculo_rota.delete("/{id_marca}", status_code=status.HTTP_200_OK)
def remover_marca(id_marca: int, db: Session = Depends(database.get_db)):
    marca = desativar_marca(db, id_marca)
    return {"mensagem": "Marca desativada com sucesso.", "id_marca": marca.id_marca, "ativo": marca.ativo}
