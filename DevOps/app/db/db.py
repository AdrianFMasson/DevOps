
from dataclasses import dataclass, field
from urllib.parse import quote_plus
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, Session
from config.Config import settings

@dataclass
class Database:
    _tunel: SSHTunnelForwarder | None = field(default=None, init=False)
    _engine: Engine | None = field(default=None, init=False)

    def start_tunnel(self):
        if self._engine is not None and self._tunel is not None and self._tunel.is_active:
            return

        self._tunel = SSHTunnelForwarder(
            (settings.ssh_host, settings.ssh_port),
            ssh_username=settings.ssh_user,
            ssh_password=settings.ssh_password,
            remote_bind_address=(settings.db_host, settings.db_port)
        )

        try:
            self._tunel.start()
            senha_codificada = quote_plus(settings.db_password)
            url = (
                f"mysql+pymysql://{settings.db_user}:{senha_codificada}"
                f"@127.0.0.1:{self._tunel.local_bind_port}"
                f"/{settings.db_name}"
            )

            self._engine = create_engine(
                url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_size=5
            )

            with self._engine.connect():
                pass

        except Exception:
            if self._engine is not None:
                self._engine.dispose()
                self._engine = None
            if self._tunel is not None:
                self._tunel.stop()
                self._tunel = None
            raise

    def get_db(self):
        if self._engine is None:
            raise RuntimeError("A conexão com o banco não foi inicializada.")

        with Session(self._engine) as sessao:
            yield sessao

    def stop_tunnel(self):
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

        if self._tunel is not None:
            self._tunel.stop()
            self._tunel = None

database = Database()
