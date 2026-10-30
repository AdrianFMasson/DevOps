
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
from fastapi.responses import Response
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
    Exige uma sessão válida para acessar
    os endpoints dos routers protegidos.
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

# Login, verificação de sessão e logout.
# Todas estão definidas em auth_rota.py.

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

# Esse router já possui sua própria validação
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
# PÁGINAS QUE EXIGEM SESSÃO AUTENTICADA
# =========================================================

PAGINAS_PROTEGIDAS = {
    "/dashboard-admin",
    "/dashboard-user",
    "/user/veiculos",
    "/user/vagas",
    "/user/clientes",
    "/clientes",
    "/veiculos",
    "/vagas",
    "/movimentacoes",
    "/usuarios",
}


# =========================================================
# SCRIPT DE VERIFICAÇÃO DA SESSÃO
# =========================================================

SCRIPT_VERIFICACAO_SESSAO = """
<script>
(function () {
    "use strict";

    let verificando = false;

    async function verificarSessao(evento) {

        if (verificando) {
            return;
        }

        verificando = true;

        // Esconde somente quando a página é restaurada
        // pelo histórico do navegador.
        if (evento && evento.persisted) {
            document.documentElement.style.visibility = "hidden";
        }

        try {

            const resposta = await fetch("/api/verificar-sessao", {
                method: "GET",
                credentials: "same-origin",
                cache: "no-store",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            if (!resposta.ok) {
                window.location.replace("/");
                return;
            }

            const resultado = await resposta.json();

            if (resultado.autenticado !== true) {
                window.location.replace("/");
                return;
            }

            // Libera a página depois da confirmação.
            document.documentElement.style.visibility = "visible";

        } catch (erro) {

            console.error("Erro ao verificar sessão:", erro);

            window.location.replace("/");

        } finally {
            verificando = false;
        }
    }


    // Verifica ao abrir ou restaurar uma página.
    window.addEventListener("pageshow", verificarSessao);


    // Esconde a página antes de ela entrar no histórico.
    window.addEventListener("pagehide", function () {
        document.documentElement.style.visibility = "hidden";
    });

})();
</script>
"""


# =========================================================
# MIDDLEWARE - CACHE E HISTÓRICO DO NAVEGADOR
# =========================================================

@app.middleware("http")
async def impedir_cache_paginas(request: Request, call_next):

    resposta = await call_next(request)

    caminho = request.url.path

    # -----------------------------------------------------
    # IMPEDIR CACHE DAS PÁGINAS
    # -----------------------------------------------------

    if not caminho.startswith("/static/"):

        resposta.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )

        resposta.headers["Pragma"] = "no-cache"
        resposta.headers["Expires"] = "0"


    # -----------------------------------------------------
    # INJETAR SCRIPT SOMENTE NAS PÁGINAS PROTEGIDAS
    # -----------------------------------------------------

    if (
        caminho not in PAGINAS_PROTEGIDAS
        or resposta.status_code != 200
        or "text/html" not in resposta.headers.get("content-type", "")
    ):
        return resposta


    # -----------------------------------------------------
    # LER O CONTEÚDO HTML
    # -----------------------------------------------------

    partes = []

    async for parte in resposta.body_iterator:
        partes.append(parte)

    conteudo = b"".join(partes)

    script = SCRIPT_VERIFICACAO_SESSAO.encode("utf-8")


    # -----------------------------------------------------
    # INSERIR SCRIPT ANTES DO FECHAMENTO DO HEAD
    # -----------------------------------------------------

    posicao = conteudo.lower().rfind(b"</head>")

    if posicao >= 0:

        conteudo = (
            conteudo[:posicao]
            + script
            + b"\n"
            + conteudo[posicao:]
        )

    else:

        conteudo = script + conteudo


    # -----------------------------------------------------
    # CRIAR NOVA RESPOSTA PRESERVANDO OS CABEÇALHOS
    # -----------------------------------------------------

    nova_resposta = Response(
        content=conteudo,
        status_code=resposta.status_code,
        background=resposta.background,
    )

    nova_resposta.raw_headers = [
        (nome, valor)
        for nome, valor in resposta.raw_headers
        if nome.lower() != b"content-length"
    ]

    nova_resposta.headers["Content-Length"] = str(len(conteudo))

    return nova_resposta
