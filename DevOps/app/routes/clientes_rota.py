
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlmodel import Session
from db.db import database
from entities.models import Client
from controller.ClientesController import listar_clientes, buscar_cliente, cadastrar_cliente, atualizar_cliente, desativar_cliente

clientes_rota = APIRouter(prefix="/api/clientes", tags=["Clientes"])

class ClienteCriacao(BaseModel):
    nome_completo: str = Field(min_length=1, max_length=150)
    documento: Optional[str] = Field(default=None, max_length=14)
    email: Optional[EmailStr] = None

class ClienteAtualizacao(BaseModel):
    nome_completo: Optional[str] = Field(default=None, min_length=1, max_length=150)
    documento: Optional[str] = Field(default=None, max_length=14)
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None

class ClienteResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_clients: int
    nome_completo: str
    documento: Optional[str]
    email: Optional[str]
    ativo: bool
    dt_cadastro: Optional[str] = None
    dt_atualizacao: Optional[str] = None

@clientes_rota.get("", response_model=list[ClienteResposta], status_code=status.HTTP_200_OK)
def obter_clientes(db: Session = Depends(database.get_db)):
    return listar_clientes(db)

@clientes_rota.get("/{id_clients}", response_model=ClienteResposta, status_code=status.HTTP_200_OK)
def obter_cliente(id_clients: int, db: Session = Depends(database.get_db)):
    return buscar_cliente(db, id_clients)

@clientes_rota.post("", response_model=ClienteResposta, status_code=status.HTTP_201_CREATED)
def criar_cliente(dados: ClienteCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_cliente(db, dados.model_dump())

@clientes_rota.put("/{id_clients}", response_model=ClienteResposta, status_code=status.HTTP_200_OK)
def editar_cliente(id_clients: int, dados: ClienteAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe pelo menos um campo para atualizar.")
    return atualizar_cliente(db, id_clients, dados_atualizados)

@clientes_rota.delete("/{id_clients}", status_code=status.HTTP_200_OK)
def excluir_cliente(id_clients: int, db: Session = Depends(database.get_db)):
    cliente = desativar_cliente(db, id_clients)
    return {"mensagem": "Cliente desativado com sucesso.", "id_clients": cliente.id_clients, "ativo": cliente.ativo}
