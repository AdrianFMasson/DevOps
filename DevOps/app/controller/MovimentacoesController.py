from datetime import datetime
from decimal import Decimal, ROUND_CEILING

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from entities.models import (
    Movimentacao,
    Veiculo,
    Vaga,
    User,
    Tarifa,
    VagaMensalista,
    Client,
    TipoVaga,
    StatusVaga,
    ModalidadeMovimentacao,
)


# =========================================================
# LISTAR MOVIMENTAÇÕES
# =========================================================

def listar_movimentacoes(
    db: Session,
    abertas: bool | None = None
):
    consulta = (
        select(Movimentacao)
        .order_by(
            Movimentacao.id_movimentacao.desc()
        )
    )

    if abertas is True:
        consulta = consulta.where(
            Movimentacao.data_hora_saida.is_(None)
        )

    elif abertas is False:
        consulta = consulta.where(
            Movimentacao.data_hora_saida.is_not(None)
        )

    return db.exec(consulta).all()


# =========================================================
# BUSCAR MOVIMENTAÇÃO
# =========================================================

def buscar_movimentacao(
    db: Session,
    id_movimentacao: int
):

    movimentacao = db.get(
        Movimentacao,
        id_movimentacao
    )

    if not movimentacao:
        raise HTTPException(
            status_code=404,
            detail="Movimentação não encontrada."
        )

    return movimentacao


# =========================================================
# HORÁRIO ATUAL
# =========================================================

def obter_data_hora_atual() -> datetime:
    """
    Retorna a data e hora local do servidor.
    Compatível com colunas DATETIME sem timezone.
    """

    return datetime.now().astimezone().replace(
        tzinfo=None
    )


# =========================================================
# VALIDAR ENTRADA
# =========================================================

def validar_entrada(
    db: Session,
    id_veiculo: int,
    id_vaga: int,
    modalidade: ModalidadeMovimentacao,
    id_tarifa: int | None = None
):

    veiculo = db.get(
        Veiculo,
        id_veiculo
    )

    if not veiculo or not veiculo.ativo:
        raise HTTPException(
            status_code=404,
            detail="Veículo inexistente ou inativo."
        )

    cliente = db.get(
        Client,
        veiculo.id_clients
    )

    if not cliente or not cliente.ativo:
        raise HTTPException(
            status_code=400,
            detail="O proprietário do veículo está inativo."
        )

    vaga = db.get(
        Vaga,
        id_vaga
    )

    if not vaga:
        raise HTTPException(
            status_code=404,
            detail="Vaga não encontrada."
        )

    if vaga.status != StatusVaga.ATIVA:
        raise HTTPException(
            status_code=400,
            detail="A vaga não está ativa."
        )

    # Verifica se o veículo já possui movimentação aberta.
    movimentacao_veiculo = db.exec(
        select(Movimentacao).where(
            Movimentacao.id_veiculo == id_veiculo,
            Movimentacao.data_hora_saida.is_(None)
        )
    ).first()

    if movimentacao_veiculo:
        raise HTTPException(
            status_code=409,
            detail="Este veículo já possui movimentação em aberto."
        )

    # Verifica se a vaga já está ocupada.
    movimentacao_vaga = db.exec(
        select(Movimentacao).where(
            Movimentacao.id_vaga == id_vaga,
            Movimentacao.data_hora_saida.is_(None)
        )
    ).first()

    if movimentacao_vaga:
        raise HTTPException(
            status_code=409,
            detail="Esta vaga já está ocupada."
        )

    tarifa = None

    # -----------------------------------------------------
    # HORISTA
    # -----------------------------------------------------

    if modalidade == ModalidadeMovimentacao.HORISTA:

        if vaga.tipo != TipoVaga.ROTATIVA:
            raise HTTPException(
                status_code=400,
                detail="Movimentação horista exige vaga rotativa."
            )

        if id_tarifa is None:
            raise HTTPException(
                status_code=400,
                detail="Informe uma tarifa para a movimentação horista."
            )

        tarifa = db.get(
            Tarifa,
            id_tarifa
        )

        agora = obter_data_hora_atual()

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
                status_code=400,
                detail="Tarifa inexistente, inativa ou fora da vigência."
            )

    # -----------------------------------------------------
    # MENSALISTA
    # -----------------------------------------------------

    elif modalidade == ModalidadeMovimentacao.MENSALISTA:

        if vaga.tipo != TipoVaga.MENSALISTA:
            raise HTTPException(
                status_code=400,
                detail="Movimentação mensalista exige vaga mensalista."
            )

        hoje = obter_data_hora_atual().date()

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
                status_code=400,
                detail=(
                    "Não existe vínculo mensalista ativo "
                    "entre o cliente e a vaga."
                )
            )

        if id_tarifa is not None:
            raise HTTPException(
                status_code=400,
                detail="Movimentação mensalista não deve ter tarifa."
            )

    return veiculo, vaga, tarifa


# =========================================================
# CALCULAR VALOR HORISTA
# =========================================================

def calcular_valor_horista(
    entrada: datetime,
    saida: datetime,
    tarifa: Tarifa
) -> Decimal:

    segundos = Decimal(
        str((saida - entrada).total_seconds())
    )

    minutos = int(
        (
            segundos / Decimal("60")
        ).to_integral_value(
            rounding=ROUND_CEILING
        )
    )

    # Período dentro da tolerância.
    if minutos <= tarifa.minutos_tolerancia:
        return Decimal("0.00")

    minutos_cobraveis = (
        minutos - tarifa.minutos_tolerancia
    )

    minutos_fracao = int(
        tarifa.minutos_fracao or 60
    )

    if minutos_fracao <= 0:
        raise HTTPException(
            status_code=400,
            detail="A configuração da fração da tarifa é inválida."
        )

    quantidade_fracoes = (
        minutos_cobraveis + minutos_fracao - 1
    ) // minutos_fracao

    valor = (
        Decimal(str(tarifa.valor_fracao))
        * Decimal(quantidade_fracoes)
    )

    return valor.quantize(
        Decimal("0.01")
    )


# =========================================================
# REGISTRAR ENTRADA
# =========================================================

def registrar_entrada(
    db: Session,
    id_veiculo: int,
    id_vaga: int,
    id_usuario_entrada: int,
    modalidade: ModalidadeMovimentacao,
    id_tarifa: int | None = None
):

    usuario = db.get(
        User,
        id_usuario_entrada
    )

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=404,
            detail="Usuário de entrada inexistente ou inativo."
        )

    veiculo, vaga, tarifa = validar_entrada(
        db=db,
        id_veiculo=id_veiculo,
        id_vaga=id_vaga,
        modalidade=modalidade,
        id_tarifa=id_tarifa
    )

    movimentacao = Movimentacao(
        id_veiculo=veiculo.id_veiculo,
        id_vaga=vaga.id_vaga,
        id_usuario_entrada=usuario.id_usuario,
        modalidade=modalidade,
        id_tarifa=tarifa.id_tarifa if tarifa else None
    )

    db.add(movimentacao)

    try:

        db.commit()
        db.refresh(movimentacao)

        return movimentacao

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Não foi possível registrar a entrada. "
                "Verifique se o veículo ou a vaga "
                "já possui movimentação em aberto."
            )
        )


# =========================================================
# REGISTRAR SAÍDA
# =========================================================

def registrar_saida(
    db: Session,
    id_movimentacao: int,
    id_usuario_saida: int
):

    movimentacao = buscar_movimentacao(
        db,
        id_movimentacao
    )

    if movimentacao.data_hora_saida is not None:
        raise HTTPException(
            status_code=409,
            detail="Esta movimentação já foi encerrada."
        )

    usuario = db.get(
        User,
        id_usuario_saida
    )

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=404,
            detail="Usuário de saída inexistente ou inativo."
        )

    saida = obter_data_hora_atual()

    entrada = movimentacao.data_hora_entrada

    if saida < entrada:
        raise HTTPException(
            status_code=400,
            detail="A saída não pode ser anterior à entrada."
        )

    valor_total = Decimal("0.00")

    # -----------------------------------------------------
    # COBRANÇA HORISTA
    # -----------------------------------------------------

    if movimentacao.modalidade == ModalidadeMovimentacao.HORISTA:

        if not movimentacao.id_tarifa:
            raise HTTPException(
                status_code=400,
                detail="Movimentação horista sem tarifa vinculada."
            )

        tarifa = db.get(
            Tarifa,
            movimentacao.id_tarifa
        )

        if not tarifa:
            raise HTTPException(
                status_code=400,
                detail="Tarifa vinculada não encontrada."
            )

        valor_total = calcular_valor_horista(
            entrada=entrada,
            saida=saida,
            tarifa=tarifa
        )

    # -----------------------------------------------------
    # MENSALISTA
    # -----------------------------------------------------

    elif movimentacao.modalidade == ModalidadeMovimentacao.MENSALISTA:

        valor_total = Decimal("0.00")

    # -----------------------------------------------------
    # SALVAR SAÍDA
    # -----------------------------------------------------

    movimentacao.id_usuario_saida = usuario.id_usuario
    movimentacao.data_hora_saida = saida
    movimentacao.valor_total = valor_total

    db.add(movimentacao)

    try:

        db.commit()
        db.refresh(movimentacao)

        return movimentacao

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Não foi possível encerrar a movimentação."
        )