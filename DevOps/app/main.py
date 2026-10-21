from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

DIRETORIO_APP = Path(__file__).resolve().parent
DIRETORIO_STATIC = DIRETORIO_APP / "static"
DIRETORIO_TEMPLATES = DIRETORIO_APP / "templates"

templates = Jinja2Templates(directory=str(DIRETORIO_TEMPLATES))

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        database.start_tunnel()
        yield
    finally:
        database.stop_tunnel()

app = FastAPI(
    title="Sistema de Estacionamento",
    description="API para gerenciamento de estacionamento",
    version="1.0.0",
    lifespan=lifespan
)

app.mount(
    "/static",
    StaticFiles(directory=str(DIRETORIO_STATIC)),
    name="static"
)

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

@app.get("/", include_in_schema=False)
def inicio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )

@app.get("/dashboard-admin", include_in_schema=False)
def dashboard_gestor(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context={}
    )

@app.get("/clientes", include_in_schema=False)
def pagina_clientes(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context={}
    )

@app.get("/veiculos", include_in_schema=False)
def pagina_veiculos(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="veiculos.html",
        context={}
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