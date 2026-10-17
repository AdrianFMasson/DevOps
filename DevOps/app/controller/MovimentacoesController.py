
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from entities.models import Movimentacao, Veiculo, Vaga, User, Tarifa, VagaMensalista, Client, TipoVaga, StatusVaga, ModalidadeMovimentacao

def listar_movimentacoes(db: Session, abertas: bool | None = None):
    consulta = select(Movimentacao).order_by(Movimentacao.id_movimentacao.desc())
    if abertas is True:
        consulta = consulta.where(Movimentacao.data_hora_saida.is_(None))
    elif abertas is False:
        consulta = consulta.where(Movimentacao.data_hora_saida.is_not(None))
    return db.exec(consulta).all()

def buscar_movimentacao(db: Session, id_movimentacao: int):
    movimentacao = db.get(Movimentacao, id_movimentacao)
    if not movimentacao:
        raise HTTPException(status_code=404, detail="Movimentação não encontrada.")
    return movimentacao

def validar_entrada(db: Session, dados):
    veiculo = db.get(Veiculo, dados.id_veiculo)
    if not veiculo or not veiculo.ativo:
        raise HTTPException(status_code=404, detail="Veículo inexistente ou inativo.")
    vaga = db.get(Vaga, dados.id_vaga)
    if not vaga:
        raise HTTPException(status_code=404, detail="Vaga não encontrada.")
    if vaga.status != StatusVaga.ATIVA:
        raise HTTPException(status_code=400, detail="A vaga não está ativa.")
    usuario = db.get(User, dados.id_usuario_entrada)
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=404, detail="Usuário de entrada inexistente ou inativo.")

    if dados.modalidade == ModalidadeMovimentacao.HORISTA:
        if vaga.tipo != TipoVaga.ROTATIVA:
            raise HTTPException(status_code=400, detail="Movimentação horista exige vaga rotativa.")
        if not dados.id_tarifa:
            raise HTTPException(status_code=400, detail="Informe uma tarifa para a movimentação horista.")
        tarifa = db.get(Tarifa, dados.id_tarifa)
        entrada = dados.data_hora_entrada or datetime.now()
        if not tarifa or not tarifa.ativo or tarifa.inicio_vigencia > entrada or (tarifa.fim_vigencia and tarifa.fim_vigencia <= entrada):
            raise HTTPException(status_code=400, detail="Tarifa inexistente, inativa ou fora da vigência.")
    elif dados.modalidade == ModalidadeMovimentacao.MENSALISTA:
        if vaga.tipo != TipoVaga.MENSALISTA:
            raise HTTPException(status_code=400, detail="Movimentação mensalista exige vaga de mensalista.")
        cliente = db.get(Client, veiculo.id_clients)
        if not cliente or not cliente.ativo:
            raise HTTPException(status_code=400, detail="O proprietário do veículo está inativo.")
        vinculo = db.exec(select(VagaMensalista).where(VagaMensalista.id_clients == veiculo.id_clients, VagaMensalista.id_vaga == vaga.id_vaga, VagaMensalista.data_fim.is_(None))).first()
        if not vinculo:
            raise HTTPException(status_code=400, detail="Não existe vínculo mensalista ativo entre o cliente e a vaga.")
        if dados.id_tarifa is not None:
            raise HTTPException(status_code=400, detail="Movimentação mensalista não deve ter tarifa.")
    return veiculo, vaga

def registrar_entrada(db: Session, dados):
    validar_entrada(db, dados)
    movimentacao = Movimentacao(**dados.model_dump())
    db.add(movimentacao)
    try:
        db.commit()
        db.refresh(movimentacao)
        return movimentacao
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível registrar a entrada. Verifique se o veículo ou a vaga já possui movimentação em aberto.")

def registrar_saida(db: Session, id_movimentacao: int, id_usuario_saida: int, data_hora_saida: datetime | None = None):
    movimentacao = buscar_movimentacao(db, id_movimentacao)
    if movimentacao.data_hora_saida is not None:
        raise HTTPException(status_code=409, detail="Esta movimentação já foi encerrada.")

    usuario = db.get(User, id_usuario_saida)
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=404, detail="Usuário de saída inexistente ou inativo.")

    saida = data_hora_saida or datetime.now()
    if saida < movimentacao.data_hora_entrada:
        raise HTTPException(status_code=400, detail="A saída não pode ser anterior à entrada.")

    if movimentacao.modalidade == ModalidadeMovimentacao.HORISTA:
        raise HTTPException(status_code=501, detail="O cálculo da cobrança horista precisa ser implementado conforme a regra de tarifação do banco. Nenhuma saída foi registrada.")

    movimentacao.id_usuario_saida = id_usuario_saida
    movimentacao.data_hora_saida = saida
    movimentacao.valor_total = Decimal("0.00")
    try:
        db.add(movimentacao)
        db.commit()
        db.refresh(movimentacao)
        return movimentacao
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Não foi possível encerrar a movimentação.")
