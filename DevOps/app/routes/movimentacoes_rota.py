
from datetime import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from db.db import database
from entities.models import (
    Client,
    Veiculo,
    MarcaVeiculo,
    ModeloVeiculo,
    Vaga,
    VagaMensalista,
    Movimentacao,
    User,
    Tarifa,
    TokenRevogado,
    TipoVaga,
    StatusVaga,
    ModalidadeMovimentacao,
)
from utils.seguranca import decodificar_token


movimentacoes_rota = APIRouter(
    prefix="/api/movimentacoes",
    tags=["Movimentações"]
)


# =========================================================
# BANCO DE DADOS
# =========================================================

def obter_db():
    yield from database.get_db()


# =========================================================
# AUTENTICAÇÃO
# =========================================================

def usuario_autenticado(
    request: Request,
    db: Session = Depends(obter_db)
) -> User:

    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão não encontrada."
        )

    try:
        payload = decodificar_token(
            token,
            tipo_esperado="access"
        )

    except (ValueError, KeyError, TypeError) as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada."
        ) from erro

    if db.get(TokenRevogado, payload["jti"]) is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão encerrada. Entre novamente."
        )

    try:
        id_usuario = int(payload["sub"])

    except (KeyError, TypeError, ValueError) as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificação da sessão inválida."
        ) from erro

    usuario = db.get(User, id_usuario)

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inexistente ou inativo."
        )

    return usuario


# =========================================================
# MODELOS DE ENTRADA
# =========================================================

class EntradaDados(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_veiculo: int = Field(gt=0)
    id_vaga: int = Field(gt=0)
    modalidade: ModalidadeMovimentacao
    id_tarifa: Optional[int] = Field(default=None, gt=0)


class SaidaDados(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================================================
# DATA E HORA
# =========================================================

def agora_local_sem_fuso() -> datetime:
    """
    O banco utiliza DATETIME sem timezone.
    Usa o horário local do servidor.
    """
    return datetime.now().astimezone().replace(tzinfo=None)


# =========================================================
# CALCULAR VALOR HORISTA
# =========================================================

def calcular_valor_horista(
    entrada: datetime,
    saida: datetime,
    tarifa: Tarifa
) -> Decimal:
    """
    Cobrança proporcional por minuto.

    Regras:
    - Tarifa de R$ 13,00 por hora (configurada no banco).
    - Tolerância de 10 minutos (configurada no banco).
    - Frações de minuto são arredondadas para o próximo minuto.
    - Valor final arredondado para duas casas decimais.
    """

    segundos = Decimal(
        str((saida - entrada).total_seconds())
    )

    if segundos <= 0:
        return Decimal("0.00")

    minutos_totais = int(
        (segundos / Decimal("60")).to_integral_value(
            rounding=ROUND_CEILING
        )
    )

    tolerancia = int(tarifa.minutos_tolerancia or 0)

    if tolerancia < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tolerância da tarifa é inválida."
        )

    if minutos_totais <= tolerancia:
        return Decimal("0.00")

    minutos_cobraveis = minutos_totais - tolerancia

    valor_hora = Decimal(str(tarifa.valor_hora))

    if valor_hora <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O valor por hora da tarifa é inválido."
        )

    valor_por_minuto = valor_hora / Decimal("60")

    valor_total = (
        valor_por_minuto * Decimal(minutos_cobraveis)
    )

    return valor_total.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# =========================================================
# CLIENTES
# =========================================================

@movimentacoes_rota.get("/clientes")
def listar_clientes(
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    clientes = db.exec(
        select(Client)
        .where(Client.ativo.is_(True))
        .order_by(Client.nome_completo)
    ).all()

    return [
        {
            "id": cliente.id_clients,
            "nome": cliente.nome_completo
        }
        for cliente in clientes
    ]


# =========================================================
# VEÍCULOS DO CLIENTE
# =========================================================

@movimentacoes_rota.get("/clientes/{id_cliente}/veiculos")
def listar_veiculos_cliente(
    id_cliente: int,
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    cliente = db.get(Client, id_cliente)

    if not cliente or not cliente.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado ou inativo."
        )

    consulta = (
        select(Veiculo, ModeloVeiculo, MarcaVeiculo)
        .join(
            ModeloVeiculo,
            ModeloVeiculo.id_modelo == Veiculo.id_modelo
        )
        .join(
            MarcaVeiculo,
            MarcaVeiculo.id_marca == ModeloVeiculo.id_marca
        )
        .where(
            Veiculo.id_clients == id_cliente,
            Veiculo.ativo.is_(True)
        )
        .order_by(Veiculo.placa)
    )

    linhas = db.exec(consulta).all()

    return [
        {
            "id": veiculo.id_veiculo,
            "placa": veiculo.placa,
            "marca": marca.nome,
            "modelo": modelo.nome,
            "cor": (
                veiculo.cor.value
                if hasattr(veiculo.cor, "value")
                else str(veiculo.cor)
            ),
            "descricao": (
                f"{veiculo.placa} — "
                f"{marca.nome} {modelo.nome}"
            )
        }
        for veiculo, modelo, marca in linhas
    ]


# =========================================================
# VAGAS DISPONÍVEIS
# =========================================================

@movimentacoes_rota.get("/veiculos/{id_veiculo}/vagas")
def listar_vagas_disponiveis(
    id_veiculo: int,
    modalidade: ModalidadeMovimentacao,
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    veiculo = db.get(Veiculo, id_veiculo)

    if not veiculo or not veiculo.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado ou inativo."
        )

    vagas_ocupadas = (
        select(Movimentacao.id_vaga)
        .where(Movimentacao.data_hora_saida.is_(None))
    )

    if modalidade == ModalidadeMovimentacao.MENSALISTA:

        hoje = agora_local_sem_fuso().date()

        consulta = (
            select(Vaga)
            .join(
                VagaMensalista,
                VagaMensalista.id_vaga == Vaga.id_vaga
            )
            .where(
                VagaMensalista.id_clients == veiculo.id_clients,
                VagaMensalista.data_fim.is_(None),
                VagaMensalista.data_inicio <= hoje,
                Vaga.tipo == TipoVaga.MENSALISTA,
                Vaga.status == StatusVaga.ATIVA,
                Vaga.id_vaga.not_in(vagas_ocupadas)
            )
            .order_by(Vaga.codigo)
        )

    else:

        consulta = (
            select(Vaga)
            .where(
                Vaga.tipo == TipoVaga.ROTATIVA,
                Vaga.status == StatusVaga.ATIVA,
                Vaga.id_vaga.not_in(vagas_ocupadas)
            )
            .order_by(Vaga.codigo)
        )

    vagas = db.exec(consulta).all()

    return [
        {
            "id": vaga.id_vaga,
            "codigo": vaga.codigo,
            "descricao": f"Vaga {vaga.codigo}"
        }
        for vaga in vagas
    ]


# =========================================================
# TARIFAS VIGENTES
# =========================================================

@movimentacoes_rota.get("/tarifas/vigentes")
def listar_tarifas_vigentes(
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    agora = agora_local_sem_fuso()

    tarifas = db.exec(
        select(Tarifa)
        .where(
            Tarifa.ativo.is_(True),
            Tarifa.inicio_vigencia <= agora,
            (
                Tarifa.fim_vigencia.is_(None)
                | (Tarifa.fim_vigencia > agora)
            )
        )
        .order_by(Tarifa.nome)
    ).all()

    return [
        {
            "id": tarifa.id_tarifa,
            "nome": tarifa.nome,
            "valor_hora": float(tarifa.valor_hora)
        }
        for tarifa in tarifas
    ]


# =========================================================
# LISTAR MOVIMENTAÇÕES
# =========================================================

@movimentacoes_rota.get("")
def listar_movimentacoes(
    abertas: Optional[bool] = None,
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    consulta = (
        select(
            Movimentacao,
            Veiculo,
            Client,
            Vaga,
            ModeloVeiculo,
            MarcaVeiculo
        )
        .join(
            Veiculo,
            Veiculo.id_veiculo == Movimentacao.id_veiculo
        )
        .join(
            Client,
            Client.id_clients == Veiculo.id_clients
        )
        .join(
            Vaga,
            Vaga.id_vaga == Movimentacao.id_vaga
        )
        .join(
            ModeloVeiculo,
            ModeloVeiculo.id_modelo == Veiculo.id_modelo
        )
        .join(
            MarcaVeiculo,
            MarcaVeiculo.id_marca == ModeloVeiculo.id_marca
        )
        .order_by(Movimentacao.id_movimentacao.desc())
    )

    if abertas is True:
        consulta = consulta.where(
            Movimentacao.data_hora_saida.is_(None)
        )

    elif abertas is False:
        consulta = consulta.where(
            Movimentacao.data_hora_saida.is_not(None)
        )

    linhas = db.exec(consulta).all()

    return [
        {
            "id": movimentacao.id_movimentacao,
            "cliente": cliente.nome_completo,
            "placa": veiculo.placa,
            "veiculo": f"{marca.nome} {modelo.nome}",
            "vaga": vaga.codigo,
            "modalidade": (
                movimentacao.modalidade.value
                if hasattr(movimentacao.modalidade, "value")
                else str(movimentacao.modalidade)
            ),
            "data_hora_entrada": (
                movimentacao.data_hora_entrada.isoformat()
                if movimentacao.data_hora_entrada
                else None
            ),
            "data_hora_saida": (
                movimentacao.data_hora_saida.isoformat()
                if movimentacao.data_hora_saida
                else None
            ),
            "valor_total": (
                float(movimentacao.valor_total)
                if movimentacao.valor_total is not None
                else None
            ),
            "aberta": movimentacao.data_hora_saida is None
        }
        for (
            movimentacao,
            veiculo,
            cliente,
            vaga,
            modelo,
            marca
        ) in linhas
    ]


# =========================================================
# REGISTRAR ENTRADA
# =========================================================

@movimentacoes_rota.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def registrar_entrada(
    dados: EntradaDados,
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    veiculo = db.get(Veiculo, dados.id_veiculo)

    if not veiculo or not veiculo.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo inexistente ou inativo."
        )

    cliente = db.get(Client, veiculo.id_clients)

    if not cliente or not cliente.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cliente do veículo está inativo."
        )

    vaga = db.get(Vaga, dados.id_vaga)

    if not vaga or vaga.status != StatusVaga.ATIVA:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vaga inexistente ou indisponível."
        )

    movimentacao_veiculo = db.exec(
        select(Movimentacao).where(
            Movimentacao.id_veiculo == veiculo.id_veiculo,
            Movimentacao.data_hora_saida.is_(None)
        )
    ).first()

    if movimentacao_veiculo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este veículo já possui uma entrada em aberto."
        )

    movimentacao_vaga = db.exec(
        select(Movimentacao).where(
            Movimentacao.id_vaga == vaga.id_vaga,
            Movimentacao.data_hora_saida.is_(None)
        )
    ).first()

    if movimentacao_vaga:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta vaga já está ocupada."
        )

    tarifa = None

    if dados.modalidade == ModalidadeMovimentacao.HORISTA:

        if vaga.tipo != TipoVaga.ROTATIVA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Horista exige vaga rotativa."
            )

        if dados.id_tarifa is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selecione uma tarifa horista."
            )

        tarifa = db.get(Tarifa, dados.id_tarifa)

        agora = agora_local_sem_fuso()

        if (
            not tarifa
            or not tarifa.ativo
            or tarifa.inicio_vigencia > agora
            or (
                tarifa.fim_vigencia
                and tarifa.fim_vigencia <= agora
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tarifa inválida ou fora da vigência."
            )

        if Decimal(str(tarifa.valor_hora)) <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O valor por hora da tarifa é inválido."
            )

    elif dados.modalidade == ModalidadeMovimentacao.MENSALISTA:

        if vaga.tipo != TipoVaga.MENSALISTA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mensalista exige vaga mensalista."
            )

        hoje = agora_local_sem_fuso().date()

        vinculo = db.exec(
            select(VagaMensalista).where(
                VagaMensalista.id_clients == veiculo.id_clients,
                VagaMensalista.id_vaga == vaga.id_vaga,
                VagaMensalista.data_inicio <= hoje,
                VagaMensalista.data_fim.is_(None)
            )
        ).first()

        if not vinculo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Não existe vínculo mensalista ativo "
                    "entre o cliente e a vaga."
                )
            )

        if dados.id_tarifa is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mensalista não utiliza tarifa horista."
            )

    movimentacao = Movimentacao(
        id_veiculo=veiculo.id_veiculo,
        id_vaga=vaga.id_vaga,
        id_usuario_entrada=usuario.id_usuario,
        modalidade=dados.modalidade,
        id_tarifa=tarifa.id_tarifa if tarifa else None
    )

    db.add(movimentacao)

    try:
        db.commit()
        db.refresh(movimentacao)

        return {
            "id": movimentacao.id_movimentacao,
            "mensagem": "Entrada registrada com sucesso."
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Veículo ou vaga já possui "
                "movimentação em aberto."
            )
        )


# =========================================================
# REGISTRAR SAÍDA
# =========================================================

@movimentacoes_rota.patch("/{id_movimentacao}/saida")
def registrar_saida(
    id_movimentacao: int,
    dados: SaidaDados,
    db: Session = Depends(obter_db),
    usuario: User = Depends(usuario_autenticado)
):

    movimentacao = db.get(
        Movimentacao,
        id_movimentacao
    )

    if not movimentacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimentação não encontrada."
        )

    if movimentacao.data_hora_saida is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta movimentação já foi encerrada."
        )

    saida = agora_local_sem_fuso()
    entrada = movimentacao.data_hora_entrada

    if entrada and saida < entrada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A saída não pode ser anterior à entrada."
        )

    valor = Decimal("0.00")

    if movimentacao.modalidade == ModalidadeMovimentacao.HORISTA:

        if not movimentacao.id_tarifa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Movimentação horista sem tarifa vinculada."
            )

        tarifa = db.get(
            Tarifa,
            movimentacao.id_tarifa
        )

        if not tarifa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tarifa vinculada não encontrada."
            )

        valor = calcular_valor_horista(
            entrada,
            saida,
            tarifa
        )

    elif movimentacao.modalidade == ModalidadeMovimentacao.MENSALISTA:

        # Mensalidade cobrada separadamente.
        # A movimentação individual não gera cobrança.
        valor = Decimal("0.00")

    movimentacao.id_usuario_saida = usuario.id_usuario
    movimentacao.data_hora_saida = saida
    movimentacao.valor_total = valor

    db.add(movimentacao)

    try:
        db.commit()
        db.refresh(movimentacao)

        return {
            "mensagem": "Saída registrada com sucesso.",
            "valor_total": float(movimentacao.valor_total)
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível encerrar a movimentação."
        )
