from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

from fastapi import (
    FastAPI,
    Request,
    Depends,
    HTTPException,
    status,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from db.db import database

from routes.auth_rota import auth_rota
from routes.usuarios_rota import usuarios_rota
from routes.clientes_rota import clientes_rota
from routes.telefones_clientes_rota import telefones_clientes_rota
from routes.marcas_veiculo_rota import marcas_veiculo_rota
from routes.modelos_veiculo_rota import modelos_veiculo_rota
from routes.veiculos_rota import veiculos_rota
from routes.vagas_rota import vagas_rota
from routes.vagas_mensalistas_rota import vagas_mensalistas_rota
from routes.tarifas_rota import tarifas_rota
from routes.movimentacoes_rota import movimentacoes_rota
from routes.admin_rota import admin_rota
from routes.user_rota import rota_user
from routes import user_rota

from entities.models import PerfilUsuario


# =========================================================
# DIRETÓRIOS
# =========================================================

DIRETORIO_APP = Path(__file__).resolve().parent
DIRETORIO_STATIC = DIRETORIO_APP / "static"
DIRETORIO_TEMPLATES = DIRETORIO_APP / "templates"

templates = Jinja2Templates(
    directory=str(DIRETORIO_TEMPLATES)
)


# =========================================================
# CICLO DE VIDA DA APLICAÇÃO
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        database.start_tunnel()
        yield
    finally:
        database.stop_tunnel()


# =========================================================
# APLICAÇÃO FASTAPI
# =========================================================

app = FastAPI(
    title="Sistema de Estacionamento",
    description="API para gerenciamento de estacionamento",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# AUTENTICAÇÃO CENTRALIZADA
# =========================================================

def exigir_usuario_autenticado(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Exige uma sessão válida para acessar os endpoints
    dos routers protegidos.
    """

    autenticacao = user_rota.obter_usuario_autenticado(
        request,
        db,
    )

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
        )

    return autenticacao["usuario"]


def exigir_administrador(
    request: Request,
    db: Session,
):
    """
    Verifica se o usuário está autenticado
    e possui perfil de administrador.
    """

    autenticacao = user_rota.obter_usuario_autenticado(
        request,
        db,
    )

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != PerfilUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente ao administrador.",
        )

    return autenticacao["usuario"]


def exigir_administrador_autenticado(
    request: Request,
    db: Session = Depends(database.get_db),
):
    """
    Dependência para proteger integralmente
    os endpoints administrativos.
    """

    usuario = exigir_administrador(request, db)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
        )

    return usuario


def contexto_administrador(usuario):
    return {
        "usuario": usuario,
        "eh_admin": True,
        "ano_atual": datetime.now().year,
    }


# =========================================================
# ARQUIVOS ESTÁTICOS
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=str(DIRETORIO_STATIC)),
    name="static",
)


# =========================================================
# ROTAS PÚBLICAS
# =========================================================

# Login e logout permanecem públicos.
app.include_router(auth_rota)


# =========================================================
# ROTAS PROTEGIDAS - USUÁRIO AUTENTICADO
# =========================================================

app.include_router(
    usuarios_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    clientes_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    telefones_clientes_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    marcas_veiculo_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    modelos_veiculo_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    veiculos_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    vagas_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    vagas_mensalistas_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    tarifas_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)

app.include_router(
    movimentacoes_rota,
    dependencies=[Depends(exigir_usuario_autenticado)],
)


# =========================================================
# ROTAS PROTEGIDAS - ADMINISTRADOR
# =========================================================

app.include_router(
    admin_rota,
    dependencies=[Depends(exigir_administrador_autenticado)],
)


# =========================================================
# ROTAS DO USUÁRIO
# =========================================================

# Esse router já possui sua própria validação de usuário
# por meio das funções existentes em user_rota.py.

app.include_router(rota_user)


# =========================================================
# PÁGINA INICIAL
# =========================================================

@app.get("/", include_in_schema=False)
def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


# =========================================================
# PÁGINAS ADMINISTRATIVAS
# =========================================================

@app.get("/clientes", include_in_schema=False)
def pagina_clientes(
    request: Request,
    db: Session = Depends(database.get_db),
):
    usuario = exigir_administrador(request, db)

    if usuario is None:
        return user_rota.redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context=contexto_administrador(usuario),
    )


@app.get("/veiculos", include_in_schema=False)
def pagina_veiculos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    usuario = exigir_administrador(request, db)

    if usuario is None:
        return user_rota.redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="veiculos.html",
        context=contexto_administrador(usuario),
    )


@app.get("/vagas", include_in_schema=False)
def pagina_vagas(
    request: Request,
    db: Session = Depends(database.get_db),
):
    usuario = exigir_administrador(request, db)

    if usuario is None:
        return user_rota.redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="vagas.html",
        context=contexto_administrador(usuario),
    )


@app.get("/movimentacoes", include_in_schema=False)
def pagina_movimentacoes(
    request: Request,
    db: Session = Depends(database.get_db),
):
    usuario = exigir_administrador(request, db)

    if usuario is None:
        return user_rota.redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="movimentacoes.html",
        context=contexto_administrador(usuario),
    )


@app.get("/usuarios", include_in_schema=False)
def pagina_usuarios(
    request: Request,
    db: Session = Depends(database.get_db),
):
    usuario = exigir_administrador(request, db)

    if usuario is None:
        return user_rota.redirecionar_login()

    return templates.TemplateResponse(
        request=request,
        name="usuarios.html",
        context=contexto_administrador(usuario),
    )


# =========================================================
# IMPEDIR CACHE DE RESPOSTAS DINÂMICAS
# =========================================================

@app.middleware("http")
async def impedir_cache_paginas(request: Request, call_next):
    resposta = await call_next(request)

    # Não interfere no cache dos arquivos estáticos.
    if not request.url.path.startswith("/static/"):
        resposta.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        resposta.headers["Pragma"] = "no-cache"
        resposta.headers["Expires"] = "0"

    return resposta