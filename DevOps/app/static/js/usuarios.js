const API_USUARIOS = "/api/usuarios";

const tabela = document.getElementById("tabelaUsuarios");
const pesquisa = document.getElementById("pesquisaUsuarios");
const filtroStatus = document.getElementById("filtroStatus");
const modal = document.getElementById("modalUsuario");
const formulario = document.getElementById("formUsuario");
const mensagem = document.getElementById("mensagem");

let usuarios = [];
let temporizadorMensagem;

async function requisicao(url, opcoes = {}) {
    const resposta = await fetch(url, {
        ...opcoes,
        headers: {
            ...(opcoes.body ? { "Content-Type": "application/json" } : {}),
            ...opcoes.headers
        }
    });

    if (!resposta.ok) {
        let detalhe = `Erro HTTP ${resposta.status}.`;

        try {
            const dados = await resposta.json();
            detalhe = typeof dados.detail === "string"
                ? dados.detail
                : JSON.stringify(dados.detail || dados);
        } catch {
            // Mantém a mensagem HTTP se a resposta não for JSON.
        }

        throw new Error(detalhe);
    }

    if (resposta.status === 204) return null;
    return resposta.json();
}

function mostrarMensagem(texto, erro = false) {
    clearTimeout(temporizadorMensagem);
    mensagem.textContent = texto;
    mensagem.classList.toggle("erro", erro);
    mensagem.classList.add("visivel");

    temporizadorMensagem = setTimeout(() => {
        mensagem.classList.remove("visivel");
    }, 4000);
}

function escaparHTML(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[caractere]);
}

function iniciais(nome) {
    return String(nome || "?")
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map(parte => parte.charAt(0))
        .join("")
        .toUpperCase();
}

function estaAtivo(usuario) {
    return usuario.ativo === true || usuario.ativo === 1;
}

function atualizarIndicadores() {
    const ativos = usuarios.filter(estaAtivo).length;
    const inativos = usuarios.length - ativos;

    document.getElementById("totalUsuarios").textContent = usuarios.length;
    document.getElementById("usuariosAtivos").textContent = ativos;
    document.getElementById("usuariosInativos").textContent = inativos;
}

function renderizarUsuarios() {
    const termo = pesquisa.value.trim().toLocaleLowerCase("pt-BR");
    const status = filtroStatus.value;

    const filtrados = usuarios.filter(usuario => {
        const correspondeTexto =
            String(usuario.nome || "").toLocaleLowerCase("pt-BR").includes(termo) ||
            String(usuario.email || "").toLocaleLowerCase("pt-BR").includes(termo) ||
            String(usuario.id_usuario || "").includes(termo);

        const correspondeStatus =
            status === "todos" ||
            (status === "ativo" && estaAtivo(usuario)) ||
            (status === "inativo" && !estaAtivo(usuario));

        return correspondeTexto && correspondeStatus;
    });

    document.getElementById("totalExibido").textContent =
        `${filtrados.length} de ${usuarios.length} operador(es)`;

    if (!filtrados.length) {
        tabela.innerHTML = `
            <tr>
                <td colspan="5" class="estado-tabela">
                    Nenhum operador encontrado.
                </td>
            </tr>`;
        return;
    }

    tabela.innerHTML = filtrados.map(usuario => {
        const ativo = estaAtivo(usuario);
        const id = Number(usuario.id_usuario);

        return `
            <tr>
                <td>
                    <div class="operador-identidade">
                        <div class="operador-avatar">${escaparHTML(iniciais(usuario.nome))}</div>
                        <div>
                            <div class="operador-nome">${escaparHTML(usuario.nome)}</div>
                            <div class="operador-tipo">ID ${escaparHTML(id)}</div>
                        </div>
                    </div>
                </td>
                <td>${escaparHTML(usuario.email)}</td>
                <td>Operador</td>
                <td>
                    <span class="status ${ativo ? "ativo" : "inativo"}">
                        ${ativo ? "Ativo" : "Inativo"}
                    </span>
                </td>
                <td>
                    <div class="acoes">
                        <button
                            class="botao-acao"
                            data-acao="editar"
                            data-id="${id}"
                        >Editar</button>
                        <button
                            class="botao-acao ${ativo ? "perigo" : "sucesso"}"
                            data-acao="${ativo ? "desativar" : "ativar"}"
                            data-id="${id}"
                        >${ativo ? "Desativar" : "Ativar"}</button>
                    </div>
                </td>
            </tr>`;
    }).join("");
}

async function carregarUsuarios() {
    tabela.innerHTML = `
        <tr><td colspan="5" class="estado-tabela">Carregando usuários...</td></tr>`;

    try {
        // O parâmetro perfil é suportado pela rota atualizada abaixo.
        const dados = await requisicao(`${API_USUARIOS}?perfil=OPERADOR`);

        // Filtragem adicional no navegador para garantir que administradores não apareçam.
        usuarios = dados.filter(usuario => usuario.perfil === "OPERADOR");

        atualizarIndicadores();
        renderizarUsuarios();
    } catch (erro) {
        tabela.innerHTML = `
            <tr><td colspan="5" class="estado-tabela">
                Não foi possível carregar os usuários.
            </td></tr>`;

        document.getElementById("totalExibido").textContent =
            "Falha ao consultar a API.";

        mostrarMensagem(erro.message || "Erro ao carregar usuários.", true);
    }
}

function abrirModal(usuario = null) {
    formulario.reset();

    const editando = Boolean(usuario);

    document.getElementById("idUsuario").value =
        usuario?.id_usuario ?? "";

    document.getElementById("nomeUsuario").value =
        usuario?.nome ?? "";

    document.getElementById("emailUsuario").value =
        usuario?.email ?? "";

    document.getElementById("tituloModal").textContent =
        editando ? "Editar usuário" : "Novo usuário";

    document.getElementById("descricaoModal").textContent =
        editando
            ? "Atualize os dados do operador."
            : "Preencha os dados para cadastrar um operador.";

    document.getElementById("senhaUsuario").required = !editando;
    document.getElementById("senhaUsuario").value = "";

    modal.classList.add("aberto");
    modal.setAttribute("aria-hidden", "false");

    document.getElementById("nomeUsuario").focus();
}

function fecharModal() {
    modal.classList.remove("aberto");
    modal.setAttribute("aria-hidden", "true");
    formulario.reset();
}

async function salvarUsuario(evento) {
    evento.preventDefault();

    const id = document.getElementById("idUsuario").value;
    const nome = document.getElementById("nomeUsuario").value.trim();
    const email = document.getElementById("emailUsuario").value.trim();
    const senha = document.getElementById("senhaUsuario").value;

    const dados = { nome, email };

    if (!id) {
        dados.perfil = "OPERADOR";
        dados.senha_hash = senha;
    } else if (senha) {
        dados.senha_hash = senha;
    }

    const botaoSalvar = document.getElementById("botaoSalvar");
    botaoSalvar.disabled = true;
    botaoSalvar.textContent = "Salvando...";

    try {
        if (id) {
            await requisicao(`${API_USUARIOS}/${id}`, {
                method: "PUT",
                body: JSON.stringify(dados)
            });
            mostrarMensagem("Usuário atualizado com sucesso.");
        } else {
            await requisicao(API_USUARIOS, {
                method: "POST",
                body: JSON.stringify(dados)
            });
            mostrarMensagem("Usuário cadastrado com sucesso.");
        }

        fecharModal();
        await carregarUsuarios();
    } catch (erro) {
        mostrarMensagem(erro.message || "Não foi possível salvar o usuário.", true);
    } finally {
        botaoSalvar.disabled = false;
        botaoSalvar.textContent = "Salvar usuário";
    }
}

async function alterarStatus(id, acao) {
    const usuario = usuarios.find(item => Number(item.id_usuario) === id);
    if (!usuario) return;

    const ativar = acao === "ativar";
    const confirmacao = ativar
        ? `Deseja reativar o usuário "${usuario.nome}"?`
        : `Deseja desativar o usuário "${usuario.nome}"?`;

    if (!confirm(confirmacao)) return;

    try {
        if (ativar) {
            await requisicao(`${API_USUARIOS}/${id}`, {
                method: "PUT",
                body: JSON.stringify({ ativo: true })
            });
        } else {
            await requisicao(`${API_USUARIOS}/${id}`, {
                method: "DELETE"
            });
        }

        mostrarMensagem(ativar
            ? "Usuário reativado com sucesso."
            : "Usuário desativado com sucesso.");

        await carregarUsuarios();
    } catch (erro) {
        mostrarMensagem(erro.message || "Não foi possível alterar o status.", true);
    }
}

document.getElementById("botaoNovo").addEventListener("click", () => abrirModal());
document.getElementById("botaoAtualizar").addEventListener("click", carregarUsuarios);
document.getElementById("botaoFechar").addEventListener("click", fecharModal);
document.getElementById("botaoCancelar").addEventListener("click", fecharModal);
formulario.addEventListener("submit", salvarUsuario);
pesquisa.addEventListener("input", renderizarUsuarios);
filtroStatus.addEventListener("change", renderizarUsuarios);

modal.addEventListener("click", evento => {
    if (evento.target === modal) fecharModal();
});

document.addEventListener("keydown", evento => {
    if (evento.key === "Escape" && modal.classList.contains("aberto")) {
        fecharModal();
    }
});

tabela.addEventListener("click", evento => {
    const botao = evento.target.closest("button[data-acao]");
    if (!botao) return;

    const id = Number(botao.dataset.id);
    const acao = botao.dataset.acao;

    if (!Number.isInteger(id) || id <= 0) return;

    if (acao === "editar") {
        const usuario = usuarios.find(item => Number(item.id_usuario) === id);
        if (usuario) abrirModal(usuario);
    } else if (acao === "ativar" || acao === "desativar") {
        alterarStatus(id, acao);
    }
});

carregarUsuarios();