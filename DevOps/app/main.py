from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
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
from routes import user_rota
from datetime import datetime

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
    lifespan=lifespan
)


# =========================================================
# ARQUIVOS ESTÁTICOS: CSS, JAVASCRIPT, IMAGENS
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory=str(DIRETORIO_STATIC)),
    name="static"
)


# =========================================================
# ROTAS DA API
# =========================================================

app.include_router(auth_rota)
app.include_router(usuarios_rota)
app.include_router(clientes_rota)
app.include_router(telefones_clientes_rota)
app.include_router(marcas_veiculo_rota)
app.include_router(modelos_veiculo_rota)
app.include_router(veiculos_rota)
app.include_router(vagas_rota)
app.include_router(vagas_mensalistas_rota)
app.include_router(tarifas_rota)
app.include_router(movimentacoes_rota)
app.include_router(user_rota.rota_user)


# =========================================================
# PÁGINA INICIAL
# =========================================================

@app.get("/", include_in_schema=False)
def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


# =========================================================
# DASHBOARD DO ADMINISTRADOR
# =========================================================

@app.get("/dashboard-admin", include_in_schema=False)
def dashboard_gestor(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context={}
    )


# =========================================================
# PÁGINAS DO SISTEMA
# =========================================================

@app.get("/clientes", include_in_schema=False)
def pagina_clientes(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context={}
    )


@app.get("/veiculos", include_in_schema=False)
def pagina_veiculos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = user_rota.obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return user_rota.redirecionar_login()

    usuario = autenticacao["usuario"]

    if usuario.perfil != PerfilUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido somente ao administrador.",
        )

    return templates.TemplateResponse(
        request=request,
        name="veiculos.html",
        context={
            "usuario": usuario,
            "ano_atual": datetime.now().year,
        },
    )


@app.get("/vagas", include_in_schema=False)
def pagina_vagas(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="vagas.html",
        context={}
    )


@app.get("/movimentacoes", include_in_schema=False)
def pagina_movimentacoes(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="movimentacoes.html",
        context={}
    )


@app.get("/usuarios", include_in_schema=False)
def pagina_usuarios(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="usuarios.html",
        context={}
    )