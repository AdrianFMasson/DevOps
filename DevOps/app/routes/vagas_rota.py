from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session
from db.db import database
from entities.models import TipoVaga, StatusVaga
from controller.VagasController import listar_vagas, buscar_vaga, cadastrar_vaga, atualizar_vaga, excluir_vaga

DIRETORIO_APP = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(DIRETORIO_APP / "templates"))

vagas_rota = APIRouter(tags=["Vagas"])

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
    dt_cadastro: Optional[datetime] = None
    dt_atualizacao: Optional[datetime] = None

@vagas_rota.get("/vagas", response_class=HTMLResponse, name="pagina_vagas", include_in_schema=False)
def pagina_vagas(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="vagas.html",
        context={"request": request, "ano_atual": datetime.now().year}
    )

@vagas_rota.get("/api/vagas", response_model=list[VagaResposta], status_code=status.HTTP_200_OK)
def obter_vagas(db: Session = Depends(database.get_db)):
    return listar_vagas(db)

@vagas_rota.get("/api/vagas/{id_vaga}", response_model=VagaResposta, status_code=status.HTTP_200_OK)
def obter_vaga(id_vaga: int, db: Session = Depends(database.get_db)):
    return buscar_vaga(db, id_vaga)

@vagas_rota.post("/api/vagas", response_model=VagaResposta, status_code=status.HTTP_201_CREATED)
def criar_vaga(dados: VagaCriacao, db: Session = Depends(database.get_db)):
    return cadastrar_vaga(db, dados.model_dump())

@vagas_rota.put("/api/vagas/{id_vaga}", response_model=VagaResposta, status_code=status.HTTP_200_OK)
def editar_vaga(id_vaga: int, dados: VagaAtualizacao, db: Session = Depends(database.get_db)):
    dados_atualizados = dados.model_dump(exclude_unset=True)
    if not dados_atualizados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe pelo menos um campo para atualizar."
        )
    return atualizar_vaga(db, id_vaga, dados_atualizados)

@vagas_rota.delete("/api/vagas/{id_vaga}", response_model=VagaResposta, status_code=status.HTTP_200_OK)
def remover_vaga(id_vaga: int, db: Session = Depends(database.get_db)):
    return excluir_vaga(db, id_vaga)