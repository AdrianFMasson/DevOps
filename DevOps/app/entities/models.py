
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, Computed, Date, DateTime, Enum as EnumSQL, ForeignKey, JSON, Numeric, SmallInteger, String, Text, text
from sqlmodel import Field, SQLModel


# ENUMS DO BANCO
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


# 1. USERS
class User(SQLModel, table=True):
    __tablename__ = "users"

    id_usuario: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(sa_type=String(120))
    email: str = Field(sa_type=String(254), unique=True, index=True)
    senha_hash: str = Field(sa_type=String(255))
    perfil: PerfilUsuario = Field(
        default=PerfilUsuario.OPERADOR,
        sa_column=Column(
            EnumSQL(PerfilUsuario, name="perfil_usuario"),
            nullable=False,
            server_default=text("'OPERADOR'")
        )
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    )


# 2. CLIENTS
class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id_clients: Optional[int] = Field(default=None, primary_key=True)
    nome_completo: str = Field(sa_type=String(150))
    documento: Optional[str] = Field(default=None, sa_type=String(14), unique=True)
    email: Optional[str] = Field(default=None, sa_type=String(254))
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    )


# 3. TELEFONES_CLIENTS
class TelefoneClient(SQLModel, table=True):
    __tablename__ = "telefones_clients"

    id_telefone: Optional[int] = Field(default=None, primary_key=True)
    id_clients: int = Field(foreign_key="clients.id_clients")
    numero: str = Field(sa_type=String(20))
    tipo: TipoTelefone = Field(
        default=TipoTelefone.CELULAR,
        sa_column=Column(
            EnumSQL(TipoTelefone, name="tipo_telefone"),
            nullable=False,
            server_default=text("'CELULAR'")
        )
    )
    nome_contato: Optional[str] = Field(default=None, sa_type=String(120))
    principal: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("0"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    telefone_principal_clients: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            Computed(
                "CASE WHEN principal = TRUE THEN id_clients ELSE NULL END",
                persisted=True
            )
        )
    )


# 4. MARCAS_VEICULO
class MarcaVeiculo(SQLModel, table=True):
    __tablename__ = "marcas_veiculo"

    id_marca: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(sa_type=String(80), unique=True)
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    )


# 5. MODELOS_VEICULO
class ModeloVeiculo(SQLModel, table=True):
    __tablename__ = "modelos_veiculo"

    id_modelo: Optional[int] = Field(default=None, primary_key=True)
    id_marca: int = Field(foreign_key="marcas_veiculo.id_marca")
    nome: str = Field(sa_type=String(100))
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    )


# 6. VEICULOS
class Veiculo(SQLModel, table=True):
    __tablename__ = "veiculos"

    id_veiculo: Optional[int] = Field(default=None, primary_key=True)
    id_clients: int = Field(foreign_key="clients.id_clients")
    id_modelo: int = Field(foreign_key="modelos_veiculo.id_modelo")
    placa: str = Field(sa_type=String(7), unique=True, index=True)
    cor: CorVeiculo = Field(
        default=CorVeiculo.OUTRA,
        sa_column=Column(
            EnumSQL(CorVeiculo, name="cor_veiculo"),
            nullable=False,
            server_default=text("'OUTRA'")
        )
    )
    ano_modelo: Optional[int] = Field(
        default=None,
        sa_column=Column(SmallInteger(unsigned=True), nullable=True)
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    )


# 7. VAGAS
class Vaga(SQLModel, table=True):
    __tablename__ = "vagas"

    id_vaga: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(sa_type=String(20), unique=True)
    tipo: TipoVaga = Field(
        sa_column=Column(EnumSQL(TipoVaga, name="tipo_vaga"), nullable=False)
    )
    status: StatusVaga = Field(
        default=StatusVaga.ATIVA,
        sa_column=Column(
            EnumSQL(StatusVaga, name="status_vaga"),
            nullable=False,
            server_default=text("'ATIVA'")
        )
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    dt_atualizacao: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"))
    )


# 8. VAGAS_MENSALISTAS
class VagaMensalista(SQLModel, table=True):
    __tablename__ = "vagas_mensalistas"

    id_vinculo: Optional[int] = Field(default=None, primary_key=True)
    id_clients: int = Field(foreign_key="clients.id_clients")
    id_vaga: int = Field(foreign_key="vagas.id_vaga")
    data_inicio: date = Field(sa_type=Date)
    data_fim: Optional[date] = Field(default=None, sa_type=Date)
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    vaga_atual_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            Computed(
                "CASE WHEN data_fim IS NULL THEN id_vaga ELSE NULL END",
                persisted=True
            )
        )
    )


# 9. TARIFAS
class Tarifa(SQLModel, table=True):
    __tablename__ = "tarifas"

    id_tarifa: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(sa_type=String(100))
    valor_hora: Decimal = Field(sa_type=Numeric(10, 2))
    minutos_tolerancia: int = Field(
        default=0,
        sa_column=Column(SmallInteger(unsigned=True), nullable=False, server_default=text("0"))
    )
    minutos_fracao: int = Field(
        default=60,
        sa_column=Column(SmallInteger(unsigned=True), nullable=False, server_default=text("60"))
    )
    valor_fracao: Decimal = Field(sa_type=Numeric(10, 2))
    inicio_vigencia: datetime = Field(sa_type=DateTime(fsp=6))
    fim_vigencia: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=True)
    )
    ativo: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, server_default=text("1"))
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )


# 10. MOVIMENTACOES
class Movimentacao(SQLModel, table=True):
    __tablename__ = "movimentacoes"

    id_movimentacao: Optional[int] = Field(default=None, primary_key=True)
    id_veiculo: int = Field(foreign_key="veiculos.id_veiculo")
    id_vaga: int = Field(foreign_key="vagas.id_vaga")
    id_usuario_entrada: int = Field(foreign_key="users.id_usuario")
    id_usuario_saida: Optional[int] = Field(
        default=None,
        foreign_key="users.id_usuario"
    )
    modalidade: ModalidadeMovimentacao = Field(
        sa_column=Column(
            EnumSQL(ModalidadeMovimentacao, name="modalidade_movimentacao"),
            nullable=False
        )
    )
    data_hora_entrada: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    data_hora_saida: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=True)
    )
    id_tarifa: Optional[int] = Field(default=None, foreign_key="tarifas.id_tarifa")
    valor_total: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 2), nullable=True)
    )
    vaga_aberta_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            Computed(
                "CASE WHEN data_hora_saida IS NULL THEN id_vaga ELSE NULL END",
                persisted=True
            )
        )
    )
    veiculo_aberto_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            Computed(
                "CASE WHEN data_hora_saida IS NULL THEN id_veiculo ELSE NULL END",
                persisted=True
            )
        )
    )
    dt_cadastro: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )


# 11. AUDITORIA
class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id_auditoria: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: Optional[int] = Field(
        default=None,
        foreign_key="users.id_usuario"
    )
    entidade: str = Field(sa_type=String(60))
    id_registro: str = Field(sa_type=String(64))
    acao: AcaoAuditoria = Field(
        sa_column=Column(EnumSQL(AcaoAuditoria, name="acao_auditoria"), nullable=False)
    )
    resultado: ResultadoAuditoria = Field(
        default=ResultadoAuditoria.SUCESSO,
        sa_column=Column(
            EnumSQL(ResultadoAuditoria, name="resultado_auditoria"),
            nullable=False,
            server_default=text("'SUCESSO'")
        )
    )
    data_hora: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(fsp=6), nullable=False, server_default=text("CURRENT_TIMESTAMP(6)"))
    )
    origem: Optional[str] = Field(default=None, sa_type=String(45))
    identificador_requisicao: Optional[str] = Field(default=None, sa_type=String(64))
    detalhes: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)
    )
