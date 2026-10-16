
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Computed,
    Date,
    Enum as EnumSQL,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, SMALLINT, DATETIME
from sqlmodel import SQLModel, Field


def enum_banco(classe_enum, nome):
    return EnumSQL(
        classe_enum,
        name=nome,
        values_callable=lambda classe: [item.value for item in classe],
    )


class PerfilUsuario(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERADOR = "OPERADOR"


class TipoTelefone(str, Enum):
    CELULAR = "CELULAR"
    FIXO = "FIXO"
    RECADO = "RECADO"


class CorVeiculo(str, Enum):
    PRETO = "PRETO"
    BRANCO = "BRANCO"
    PRATA = "PRATA"
    CINZA = "CINZA"
    VERMELHO = "VERMELHO"
    AZUL = "AZUL"
    VERDE = "VERDE"
    AMARELO = "AMARELO"
    MARROM = "MARROM"
    BEGE = "BEGE"
    DOURADO = "DOURADO"
    OUTRA = "OUTRA"


class TipoVaga(str, Enum):
    MENSALISTA = "MENSALISTA"
    ROTATIVA = "ROTATIVA"


class StatusVaga(str, Enum):
    ATIVA = "ATIVA"
    BLOQUEADA = "BLOQUEADA"
    INATIVA = "INATIVA"


class ModalidadeMovimentacao(str, Enum):
    MENSALISTA = "MENSALISTA"
    HORISTA = "HORISTA"


class AcaoAuditoria(str, Enum):
    CRIACAO = "CRIACAO"
    ALTERACAO = "ALTERACAO"
    DESATIVACAO = "DESATIVACAO"
    EXCLUSAO = "EXCLUSAO"


class ResultadoAuditoria(str, Enum):
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id_usuario: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    nome: str = Field(sa_type=String(120))
    email: str = Field(sa_column=Column(String(254), unique=True, nullable=False))
    senha_hash: str = Field(sa_type=String(255))
    perfil: PerfilUsuario = Field(
        default=PerfilUsuario.OPERADOR,
        sa_column=Column(
            enum_banco(PerfilUsuario, "perfil_usuario"),
            nullable=False,
            server_default=text("'OPERADOR'"),
        ),
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
    )


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id_clients: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    nome_completo: str = Field(sa_type=String(150))
    documento: Optional[str] = Field(
        default=None,
        sa_column=Column(String(14), unique=True, nullable=True),
    )
    email: Optional[str] = Field(
        default=None,
        sa_column=Column(String(254), nullable=True),
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
    )


class TelefoneClient(SQLModel, table=True):
    __tablename__ = "telefones_clients"

    id_telefone: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    id_clients: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("clients.id_clients"),
            nullable=False,
        )
    )
    numero: str = Field(sa_type=String(20))
    tipo: TipoTelefone = Field(
        default=TipoTelefone.CELULAR,
        sa_column=Column(
            enum_banco(TipoTelefone, "tipo_telefone"),
            nullable=False,
            server_default=text("'CELULAR'"),
        ),
    )
    nome_contato: Optional[str] = Field(
        default=None,
        sa_column=Column(String(120), nullable=True),
    )
    principal: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("0")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    telefone_principal_clients: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            Computed(
                "CASE WHEN principal = 1 THEN id_clients ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
            unique=True,
        ),
    )


class MarcaVeiculo(SQLModel, table=True):
    __tablename__ = "marcas_veiculo"

    id_marca: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    nome: str = Field(
        sa_column=Column(String(80), unique=True, nullable=False)
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
    )


class ModeloVeiculo(SQLModel, table=True):
    __tablename__ = "modelos_veiculo"

    id_modelo: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    id_marca: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("marcas_veiculo.id_marca"),
            nullable=False,
        )
    )
    nome: str = Field(sa_type=String(100))
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
    )


class Veiculo(SQLModel, table=True):
    __tablename__ = "veiculos"

    id_veiculo: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    id_clients: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("clients.id_clients"),
            nullable=False,
        )
    )
    id_modelo: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("modelos_veiculo.id_modelo"),
            nullable=False,
        )
    )
    placa: str = Field(
        sa_column=Column(String(7), unique=True, nullable=False)
    )
    cor: CorVeiculo = Field(
        default=CorVeiculo.OUTRA,
        sa_column=Column(
            enum_banco(CorVeiculo, "cor_veiculo"),
            nullable=False,
            server_default=text("'OUTRA'"),
        ),
    )
    ano_modelo: Optional[int] = Field(
        default=None,
        sa_column=Column(SMALLINT(unsigned=True), nullable=True),
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
    )


class Vaga(SQLModel, table=True):
    __tablename__ = "vagas"

    id_vaga: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    codigo: str = Field(
        sa_column=Column(String(20), unique=True, nullable=False)
    )
    tipo: TipoVaga = Field(
        sa_column=Column(
            enum_banco(TipoVaga, "tipo_vaga"),
            nullable=False,
        )
    )
    status: StatusVaga = Field(
        default=StatusVaga.ATIVA,
        sa_column=Column(
            enum_banco(StatusVaga, "status_vaga"),
            nullable=False,
            server_default=text("'ATIVA'"),
        ),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text(
                "CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"
            ),
        ),
    )


class VagaMensalista(SQLModel, table=True):
    __tablename__ = "vagas_mensalistas"

    id_vinculo: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    id_clients: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("clients.id_clients"),
            nullable=False,
        )
    )
    id_vaga: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("vagas.id_vaga"),
            nullable=False,
        )
    )
    data_inicio: date = Field(sa_type=Date)
    data_fim: Optional[date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    vaga_atual_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            Computed(
                "CASE WHEN data_fim IS NULL THEN id_vaga ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
            unique=True,
        ),
    )


class Tarifa(SQLModel, table=True):
    __tablename__ = "tarifas"

    id_tarifa: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    nome: str = Field(sa_type=String(100))
    valor_hora: Decimal = Field(sa_type=Numeric(10, 2))
    minutos_tolerancia: int = Field(
        default=0,
        sa_column=Column(
            SMALLINT(unsigned=True),
            nullable=False,
            server_default=text("0"),
        ),
    )
    minutos_fracao: int = Field(
        default=60,
        sa_column=Column(
            SMALLINT(unsigned=True),
            nullable=False,
            server_default=text("60"),
        ),
    )
    valor_fracao: Decimal = Field(sa_type=Numeric(10, 2))
    inicio_vigencia: datetime = Field(sa_type=DATETIME(fsp=6))
    fim_vigencia: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DATETIME(fsp=6), nullable=True),
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1")),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )


class Movimentacao(SQLModel, table=True):
    __tablename__ = "movimentacoes"

    id_movimentacao: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    id_veiculo: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("veiculos.id_veiculo"),
            nullable=False,
        )
    )
    id_vaga: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("vagas.id_vaga"),
            nullable=False,
        )
    )
    id_usuario_entrada: int = Field(
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("users.id_usuario"),
            nullable=False,
        )
    )
    id_usuario_saida: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("users.id_usuario"),
            nullable=True,
        ),
    )
    modalidade: ModalidadeMovimentacao = Field(
        sa_column=Column(
            enum_banco(ModalidadeMovimentacao, "modalidade_movimentacao"),
            nullable=False,
        )
    )
    data_hora_entrada: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    data_hora_saida: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DATETIME(fsp=6), nullable=True),
    )
    id_tarifa: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("tarifas.id_tarifa"),
            nullable=True,
        ),
    )
    valor_total: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 2), nullable=True),
    )
    vaga_aberta_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            Computed(
                "CASE WHEN data_hora_saida IS NULL THEN id_vaga ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
            unique=True,
        ),
    )
    veiculo_aberto_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            Computed(
                "CASE WHEN data_hora_saida IS NULL THEN id_veiculo ELSE NULL END",
                persisted=True,
            ),
            nullable=True,
            unique=True,
        ),
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id_auditoria: Optional[int] = Field(
        default=None,
        sa_column=Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True),
    )
    id_usuario: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BIGINT(unsigned=True),
            ForeignKey("users.id_usuario", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    entidade: str = Field(sa_type=String(60))
    id_registro: str = Field(sa_type=String(64))
    acao: AcaoAuditoria = Field(
        sa_column=Column(
            enum_banco(AcaoAuditoria, "acao_auditoria"),
            nullable=False,
        )
    )
    resultado: ResultadoAuditoria = Field(
        default=ResultadoAuditoria.SUCESSO,
        sa_column=Column(
            enum_banco(ResultadoAuditoria, "resultado_auditoria"),
            nullable=False,
            server_default=text("'SUCESSO'"),
        ),
    )
    data_hora: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DATETIME(fsp=6),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP(6)"),
        ),
    )
    origem: Optional[str] = Field(
        default=None,
        sa_column=Column(String(45), nullable=True),
    )
    identificador_requisicao: Optional[str] = Field(
        default=None,
        sa_column=Column(String(64), nullable=True),
    )
    detalhes: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
