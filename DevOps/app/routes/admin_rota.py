
from datetime import datetime, time, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from db.db import database
from entities.models import (
    PerfilUsuario,
    Movimentacao,
    Veiculo,
    ModeloVeiculo,
    Client,
    Vaga,
)
from routes.user_rota import obter_usuario_autenticado


admin_rota = APIRouter()

DIRETORIO_TEMPLATES = (
    Path(__file__).resolve().parent.parent / "templates"
)

templates = Jinja2Templates(
    directory=str(DIRETORIO_TEMPLATES)
)


@admin_rota.get("/dashboard-admin", include_in_schema=False)
def dashboard_gestor(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        resposta = RedirectResponse(
            url="/login",
            status_code=status.HTTP_303_SEE_OTHER,
        )
        resposta.delete_cookie("access_token", path="/")
        return resposta

    if autenticacao["perfil"] != PerfilUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente ao administrador.",
        )

    # Define o intervalo do dia atual.
    agora = datetime.now()
    inicio_dia = datetime.combine(agora.date(), time.min)
    inicio_proximo_dia = inicio_dia + timedelta(days=1)

    # Busca movimentações de hoje e seus respectivos dados.
    consulta = (
        select(
            Movimentacao,
            Veiculo,
            ModeloVeiculo,
            Client,
            Vaga,
        )
        .join(
            Veiculo,
            Movimentacao.id_veiculo == Veiculo.id_veiculo,
        )
        .join(
            ModeloVeiculo,
            Veiculo.id_modelo == ModeloVeiculo.id_modelo,
        )
        .join(
            Client,
            Veiculo.id_clients == Client.id_clients,
        )
        .outerjoin(
            Vaga,
            Movimentacao.id_vaga == Vaga.id_vaga,
        )
        .where(
            Movimentacao.data_hora_entrada >= inicio_dia,
            Movimentacao.data_hora_entrada < inicio_proximo_dia,
        )
        .order_by(Movimentacao.data_hora_entrada.desc())
    )

    resultados = db.exec(consulta).all()

    movimentacoes = []

    for movimentacao, veiculo, modelo, cliente, vaga in resultados:
        movimentacoes.append({
            "modelo_veiculo": modelo.nome,
            "placa": veiculo.placa,
            "nome_cliente": cliente.nome_completo,
            "codigo_vaga": vaga.codigo if vaga else None,
            "data_hora_entrada": (
                movimentacao.data_hora_entrada.strftime("%d/%m/%Y %H:%M")
                if movimentacao.data_hora_entrada
                else None
            ),
            "data_hora_saida": (
                movimentacao.data_hora_saida.strftime("%d/%m/%Y %H:%M")
                if movimentacao.data_hora_saida
                else None
            ),
        })

    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context={
            "usuario": autenticacao["usuario"],
            "ano_atual": agora.year,
            "movimentacoes": movimentacoes,
        },
    )
