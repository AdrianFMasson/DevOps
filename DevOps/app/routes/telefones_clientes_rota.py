
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import TipoTelefone
from controller.TelefonesClientesController import listar_telefones, buscar_telefone, cadastrar_telefone, atualizar_telefone, excluir_telefone

telefones_clientes_rota = APIRouter(prefix="/api/telefones-clientes", tags=["Telefones de clientes"])

class TelefoneCriacao(BaseModel):
    id_clients: int = Field(gt=0)
    numero: str = Field(min_length=8, max_length=20)
    tipo: TipoTelefone = TipoTelefone.CELULAR
    nome_contato: Optional[str] = Field(default=None, max_length=120)
    principal: bool = False

class TelefoneAtualizacao(BaseModel):
    id_clients: Optional[int] = Field(default=None, gt=0)
    numero: Optional[str] = Field(default=None, min_length=8, max_length=20)
    tipo: Optional[TipoTelefone] = None
    nome_contato: Optional[str] = Field(default=None, max_length=120)
    principal: Optional[bool] = None

class TelefoneResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_telefone: int
    id_clients: int
    numero: str
    tipo: TipoTelefone
    nome_contato: Optional[str]
    principal: bool
    dt_cadastro: Optional[str] = None
    telefone_principal_clients: Optional[int] = None

@telefones_clientes_rota.get("", response_model=list[TelefoneResposta], status_code=status.HTTP_200_OK)
def obter_telefones(db: Session = Depends(database.get_db)):
    return listar_telefones(db)

@telefones_clientes_rota.get("/{id_telefone}", response_model=TelefoneResposta, status_code=status.HTTP_200_OK)
def obter_telefone(id_telefone: int, db: Session = Depends(database.get_db)):
    return buscar_telefone(db, id_telefone)

@telefones_clientes_rota.post("", response_model=TelefoneResposta, status_code=status.HTTP_201_CREATED)
def criar_telefone(dados: TelefoneCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_telefone(db, dados.model_dump())

@telefones_clientes_rota.put("/{id_telefone}", response_model=TelefoneResposta, status_code=status.HTTP_200_OK)
def editar_telefone(id_telefone: int, dados: TelefoneAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe pelo menos um campo para atualizar.")
    return atualizar_telefone(db, id_telefone, dados_atualizados)

@telefones_clientes_rota.delete("/{id_telefone}", status_code=status.HTTP_200_OK)
def remover_telefone(id_telefone: int, db: Session = Depends(database.get_db)):
    excluir_telefone(db, id_telefone)
    return {"mensagem": "Telefone excluído com sucesso.", "id_telefone": id_telefone}
