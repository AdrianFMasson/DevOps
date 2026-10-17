
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import ModalidadeMovimentacao, Movimentacao
from controller import MovimentacoesController

movimentacoes_rota = APIRouter(prefix="/api/movimentacoes", tags=["Movimentações"])

def obter_db():
    yield from database.get_db()

class MovimentacaoEntrada(BaseModel):
    id_veiculo: int = Field(gt=0)
    id_vaga: int = Field(gt=0)
    id_usuario_entrada: int = Field(gt=0)
    modalidade: ModalidadeMovimentacao
    data_hora_entrada: Optional[datetime] = None
    id_tarifa: Optional[int] = None

class MovimentacaoSaida(BaseModel):
    id_usuario_saida: int = Field(gt=0)
    data_hora_saida: Optional[datetime] = None

class MovimentacaoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_movimentacao: int
    id_veiculo: int
    id_vaga: int
    id_usuario_entrada: int
    id_usuario_saida: Optional[int] = None
    modalidade: ModalidadeMovimentacao
    data_hora_entrada: datetime
    data_hora_saida: Optional[datetime] = None
    id_tarifa: Optional[int] = None
    valor_total: Optional[float] = None
    dt_cadastro: datetime

@movimentacoes_rota.get("", response_model=list[MovimentacaoResposta])
def listar_movimentacoes(abertas: Optional[bool] = Query(default=None), db: Session = Depends(obter_db)):
    return MovimentacoesController.listar_movimentacoes(db, abertas)

@movimentacoes_rota.get("/{id_movimentacao}", response_model=MovimentacaoResposta)
def buscar_movimentacao(id_movimentacao: int, db: Session = Depends(obter_db)):
    return MovimentacoesController.buscar_movimentacao(db, id_movimentacao)

@movimentacoes_rota.post("", response_model=MovimentacaoResposta, status_code=201)
def registrar_entrada(dados: MovimentacaoEntrada, db: Session = Depends(obter_db)):
    return MovimentacoesController.registrar_entrada(db, dados)

@movimentacoes_rota.patch("/{id_movimentacao}/saida", response_model=MovimentacaoResposta)
def registrar_saida(id_movimentacao: int, dados: MovimentacaoSaida, db: Session = Depends(obter_db)):
    return MovimentacoesController.registrar_saida(db, id_movimentacao, dados.id_usuario_saida, dados.data_hora_saida)
