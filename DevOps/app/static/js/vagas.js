
"use strict";

const API_VAGAS = "/api/vagas";
const TIPOS_VAGA = { MENSALISTA: "Mensalista", ROTATIVA: "Rotativa" };
const STATUS_VAGA = { ATIVA: "Ativa", BLOQUEADA: "Bloqueada", INATIVA: "Inativa" };

document.addEventListener("DOMContentLoaded", () => {
    const elemento = id => document.getElementById(id);
    const perfilUsuario = (document.body.dataset.perfil || "").trim().toUpperCase();
    const ehAdministrador = perfilUsuario === "ADMINISTRADOR";

    const listaVagas = elemento("lista-vagas");
    const campoPesquisa = elemento("pesquisa-vagas");
    const mensagemLista = elemento("mensagem-lista-vagas");
    const modalVaga = elemento("modal-vaga");
    const formularioVaga = elemento("formulario-vaga");
    const tituloModalVaga = elemento("titulo-modal-vaga");
    const descricaoModalVaga = elemento("descricao-modal-vaga");
    const campoId = elemento("id-vaga");
    const campoCodigo = elemento("codigo-vaga");
    const campoTipo = elemento("tipo-vaga");
    const campoStatus = elemento("status-vaga");
    const mensagemFormulario = elemento("mensagem-formulario-vaga");
    const botaoSalvar = elemento("botao-salvar-vaga");
    const modalStatus = elemento("modal-status-vaga");
    const formularioStatus = elemento("formulario-status-vaga");
    const campoIdStatus = elemento("id-status-vaga");
    const campoNovoStatus = elemento("novo-status-vaga");
    const mensagemStatus = elemento("mensagem-status-vaga");
    const botaoConfirmarStatus = elemento("botao-confirmar-status");
    const modalExclusao = elemento("modal-exclusao-vaga");
    const textoExclusao = elemento("texto-exclusao-vaga");
    const mensagemExclusao = elemento("mensagem-exclusao-vaga");
    const botaoConfirmarExclusao = elemento("botao-confirmar-exclusao");
    const botaoTema = elemento("botao-tema");
    const botaoNovaVaga = elemento("botao-nova-vaga");

    let vagas = [];
    let carregando = false;
    let vagaParaExcluir = null;
    let modalAnterior = null;

    if (!listaVagas || !campoPesquisa) {
        console.error("Os elementos HTML necessários para consultar vagas não foram encontrados.");
        return;
    }

    // Segurança adicional na interface: operador somente consulta.
    if (!ehAdministrador) {
        if (botaoNovaVaga) botaoNovaVaga.hidden = true;
        if (modalVaga) modalVaga.hidden = true;
        if (modalStatus) modalStatus.hidden = true;
        if (modalExclusao) modalExclusao.hidden = true;
    }

    function mostrarMensagem(elementoMensagem, texto, tipo = "") {
        if (!elementoMensagem) return;
        elementoMensagem.textContent = texto;
        elementoMensagem.classList.remove("erro", "sucesso");
        if (tipo) elementoMensagem.classList.add(tipo);
    }

    async function requisicaoAPI(url, opcoes = {}) {
        const resposta = await fetch(url, {
            credentials: "same-origin",
            ...opcoes,
            headers: {
                ...(opcoes.body ? { "Content-Type": "application/json" } : {}),
                ...opcoes.headers
            }
        });

        const texto = await resposta.text();
        let dados = null;

        if (texto) {
            try {
                dados = JSON.parse(texto);
            } catch {
                dados = { detail: texto };
            }
        }

        if (!resposta.ok) {
            const detalhe = dados?.detail || dados?.mensagem || `Erro HTTP ${resposta.status}.`;
            throw new Error(
                Array.isArray(detalhe)
                    ? detalhe.map(item => item.msg || String(item)).join(", ")
                    : String(detalhe)
            );
        }

        return dados;
    }

    function obterId(vaga) {
        return vaga.id_vaga ?? vaga.id;
    }

    function obterCodigo(vaga) {
        return vaga.codigo ?? "";
    }

    function obterTipo(vaga) {
        return String(vaga.tipo ?? "").toUpperCase();
    }

    function obterStatus(vaga) {
        return String(vaga.status ?? "").toUpperCase();
    }

    function formatarData(valor) {
        if (!valor) return "—";

        const data = new Date(valor);
        if (Number.isNaN(data.getTime())) return String(valor);

        return new Intl.DateTimeFormat("pt-BR", {
            dateStyle: "short",
            timeStyle: "short"
        }).format(data);
    }

    function criarCelula(texto, classe = "") {
        const celula = document.createElement("td");
        celula.textContent = texto || "—";
        if (classe) celula.className = classe;
        return celula;
    }

    function criarBotao(texto, classe, rotulo, acao, id) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = `botao-acao-vaga ${classe}`.trim();
        botao.textContent = texto;
        botao.setAttribute("aria-label", rotulo);
        botao.addEventListener("click", () => acao(id));
        return botao;
    }

    function criarEtiqueta(texto, classe) {
        const etiqueta = document.createElement("span");
        etiqueta.className = classe;
        etiqueta.textContent = texto;
        return etiqueta;
    }

    function renderizarResumo() {
        elemento("total-vagas").textContent = vagas.length;
        elemento("vagas-ativas").textContent =
            vagas.filter(vaga => obterStatus(vaga) === "ATIVA").length;
        elemento("vagas-bloqueadas").textContent =
            vagas.filter(vaga => obterStatus(vaga) === "BLOQUEADA").length;
        elemento("vagas-inativas").textContent =
            vagas.filter(vaga => obterStatus(vaga) === "INATIVA").length;
    }

    function renderizarVagas() {
        const pesquisa = (campoPesquisa.value || "").trim().toLocaleLowerCase("pt-BR");

        const filtradas = vagas.filter(vaga => {
            const conteudo = [
                obterCodigo(vaga),
                TIPOS_VAGA[obterTipo(vaga)] || obterTipo(vaga),
                STATUS_VAGA[obterStatus(vaga)] || obterStatus(vaga)
            ].join(" ").toLocaleLowerCase("pt-BR");

            return conteudo.includes(pesquisa);
        });

        listaVagas.replaceChildren();

        if (filtradas.length === 0) {
            const linha = document.createElement("tr");
            const celula = document.createElement("td");
            const titulo = document.createElement("strong");
            const descricao = document.createElement("span");

            celula.colSpan = 6;
            celula.className = "mensagem-vazia";
            titulo.textContent = pesquisa
                ? "Nenhuma vaga encontrada"
                : "Nenhuma vaga cadastrada";
            descricao.textContent = pesquisa
                ? "Tente pesquisar usando outros termos."
                : "Ainda não existem vagas cadastradas.";

            celula.append(titulo, descricao);
            linha.appendChild(celula);
            listaVagas.appendChild(linha);
            return;
        }

        filtradas.forEach(vaga => {
            const linha = document.createElement("tr");
            const id = obterId(vaga);
            const codigo = obterCodigo(vaga);
            const status = obterStatus(vaga);

            linha.appendChild(criarCelula(codigo, "codigo-vaga-tabela"));

            const celulaTipo = document.createElement("td");
            celulaTipo.appendChild(criarEtiqueta(
                TIPOS_VAGA[obterTipo(vaga)] || obterTipo(vaga) || "—",
                "etiqueta-tipo"
            ));
            linha.appendChild(celulaTipo);

            const celulaStatus = document.createElement("td");
            celulaStatus.appendChild(criarEtiqueta(
                STATUS_VAGA[status] || status || "—",
                `etiqueta-status ${status.toLowerCase()}`
            ));
            linha.appendChild(celulaStatus);

            linha.appendChild(criarCelula(formatarData(vaga.dt_cadastro)));
            linha.appendChild(criarCelula(formatarData(vaga.dt_atualizacao)));

            const celulaAcoes = document.createElement("td");

            if (ehAdministrador) {
                const acoes = document.createElement("div");
                acoes.className = "acoes-vaga";

                acoes.appendChild(criarBotao(
                    "Editar", "", `Editar vaga ${codigo}`, editarVaga, id
                ));

                acoes.appendChild(criarBotao(
                    "Status", "status",
                    `Alterar status da vaga ${codigo}`,
                    abrirModalStatus, id
                ));

                acoes.appendChild(criarBotao(
                    "Excluir", "excluir",
                    `Excluir vaga ${codigo}`,
                    abrirModalExclusao, id
                ));

                celulaAcoes.appendChild(acoes);
            } else {
                const consulta = document.createElement("span");
                consulta.className = "acoes-somente-consulta";
                consulta.textContent = "Somente consulta";
                celulaAcoes.appendChild(consulta);
            }

            linha.appendChild(celulaAcoes);
            listaVagas.appendChild(linha);
        });
    }

    async function carregarVagas() {
        if (carregando) return;

        carregando = true;
        listaVagas.innerHTML = `
            <tr>
                <td colspan="6" class="mensagem-vazia">
                    <strong>Carregando vagas...</strong>
                    <span>Aguarde enquanto consultamos os registros.</span>
                </td>
            </tr>
        `;
        mostrarMensagem(mensagemLista, "");

        try {
            const dados = await requisicaoAPI(API_VAGAS);
            vagas = Array.isArray(dados) ? dados : dados?.vagas ?? dados?.items ?? [];

            if (!Array.isArray(vagas)) {
                throw new Error("A API não retornou uma lista válida de vagas.");
            }

            renderizarResumo();
            renderizarVagas();
        } catch (erro) {
            console.error("Erro ao carregar vagas:", erro);

            listaVagas.innerHTML = `
                <tr>
                    <td colspan="6" class="mensagem-vazia">
                        <strong>Não foi possível carregar as vagas.</strong>
                        <span>Verifique a conexão com o servidor e tente novamente.</span>
                    </td>
                </tr>
            `;

            mostrarMensagem(
                mensagemLista,
                erro.message || "Não foi possível carregar as vagas.",
                "erro"
            );

            ["total-vagas", "vagas-ativas", "vagas-bloqueadas", "vagas-inativas"]
                .forEach(id => {
                    const campo = elemento(id);
                    if (campo) campo.textContent = "—";
                });
        } finally {
            carregando = false;
        }
    }

    function exigirAdministrador() {
        if (ehAdministrador) return true;

        mostrarMensagem(
            mensagemLista,
            "Seu perfil permite somente consultar vagas.",
            "erro"
        );
        return false;
    }

    function abrirModal(modal) {
        if (!ehAdministrador || !modal) return;

        modalAnterior = document.activeElement;
        modal.hidden = false;
        document.body.classList.add("modal-aberto");

        const foco = modal.querySelector("input:not([type=hidden]), select, button");
        window.setTimeout(() => foco?.focus(), 0);
    }

    function fecharModal(modal) {
        if (!modal || modal.hidden) return;

        modal.hidden = true;

        if (![modalVaga, modalStatus, modalExclusao]
            .filter(Boolean)
            .some(item => !item.hidden)) {
            document.body.classList.remove("modal-aberto");
        }

        modalAnterior?.focus?.();
    }

    function abrirFormulario(vaga = null) {
        if (!exigirAdministrador()) return;
        if (!formularioVaga || !modalVaga) return;

        formularioVaga.reset();
        campoId.value = vaga ? String(obterId(vaga) ?? "") : "";
        campoCodigo.value = vaga ? obterCodigo(vaga) : "";
        campoTipo.value = vaga ? obterTipo(vaga) : "ROTATIVA";
        campoStatus.value = vaga ? obterStatus(vaga) : "ATIVA";

        tituloModalVaga.textContent = vaga ? "Editar vaga" : "Nova vaga";
        descricaoModalVaga.textContent = vaga
            ? `Atualize os dados da vaga ${obterCodigo(vaga)}.`
            : "Informe os dados da nova vaga.";

        botaoSalvar.textContent = vaga ? "Salvar alterações" : "Cadastrar vaga";
        mostrarMensagem(mensagemFormulario, "");
        abrirModal(modalVaga);
    }

    function editarVaga(id) {
        if (!exigirAdministrador()) return;

        const vaga = vagas.find(item => String(obterId(item)) === String(id));

        if (!vaga) {
            mostrarMensagem(mensagemLista, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }

        abrirFormulario(vaga);
    }

    function abrirModalStatus(id) {
        if (!exigirAdministrador()) return;

        const vaga = vagas.find(item => String(obterId(item)) === String(id));

        if (!vaga || !formularioStatus || !modalStatus) {
            mostrarMensagem(mensagemLista, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }

        formularioStatus.reset();
        campoIdStatus.value = String(obterId(vaga));
        campoNovoStatus.value = obterStatus(vaga);

        elemento("descricao-status-vaga").textContent =
            `Vaga ${obterCodigo(vaga)} — status atual: ${
                STATUS_VAGA[obterStatus(vaga)] || obterStatus(vaga)
            }.`;

        mostrarMensagem(mensagemStatus, "");
        abrirModal(modalStatus);
    }

    function abrirModalExclusao(id) {
        if (!exigirAdministrador()) return;

        const vaga = vagas.find(item => String(obterId(item)) === String(id));

        if (!vaga || !modalExclusao) {
            mostrarMensagem(mensagemLista, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }

        vagaParaExcluir = vaga;
        textoExclusao.textContent =
            `Você está prestes a excluir a vaga ${obterCodigo(vaga)}. ` +
            "Se estiver vinculada a outros registros, o servidor poderá impedir a exclusão. " +
            "Esta ação não poderá ser desfeita.";

        mostrarMensagem(mensagemExclusao, "");
        botaoConfirmarExclusao.disabled = false;
        abrirModal(modalExclusao);
    }

    async function salvarVaga(evento) {
        evento.preventDefault();
        if (!exigirAdministrador()) return;

        const codigo = campoCodigo.value.trim();
        const id = campoId.value.trim();

        if (!codigo) {
            mostrarMensagem(mensagemFormulario, "Informe o código da vaga.", "erro");
            return;
        }

        const editando = Boolean(id);
        const dados = {
            codigo,
            tipo: campoTipo.value,
            status: campoStatus.value
        };

        botaoSalvar.disabled = true;
        botaoSalvar.textContent = editando ? "Salvando..." : "Cadastrando...";
        mostrarMensagem(mensagemFormulario, "");

        try {
            await requisicaoAPI(
                editando
                    ? `${API_VAGAS}/${encodeURIComponent(id)}`
                    : API_VAGAS,
                {
                    method: editando ? "PUT" : "POST",
                    body: JSON.stringify(dados)
                }
            );

            fecharModal(modalVaga);
            mostrarMensagem(
                mensagemLista,
                editando ? "Vaga atualizada com sucesso." : "Vaga cadastrada com sucesso.",
                "sucesso"
            );
            await carregarVagas();
        } catch (erro) {
            console.error("Erro ao salvar vaga:", erro);
            mostrarMensagem(
                mensagemFormulario,
                erro.message || "Não foi possível salvar a vaga.",
                "erro"
            );
        } finally {
            botaoSalvar.disabled = false;
            botaoSalvar.textContent = campoId.value ? "Salvar alterações" : "Cadastrar vaga";
        }
    }

    async function salvarStatus(evento) {
        evento.preventDefault();
        if (!exigirAdministrador()) return;

        const id = campoIdStatus.value;
        const vaga = vagas.find(item => String(obterId(item)) === String(id));

        if (!vaga) {
            mostrarMensagem(mensagemStatus, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }

        botaoConfirmarStatus.disabled = true;
        botaoConfirmarStatus.textContent = "Salvando...";
        mostrarMensagem(mensagemStatus, "");

        try {
            await requisicaoAPI(`${API_VAGAS}/${encodeURIComponent(id)}`, {
                method: "PUT",
                body: JSON.stringify({ status: campoNovoStatus.value })
            });

            fecharModal(modalStatus);
            mostrarMensagem(
                mensagemLista,
                `Status da vaga ${obterCodigo(vaga)} atualizado com sucesso.`,
                "sucesso"
            );
            await carregarVagas();
        } catch (erro) {
            console.error("Erro ao alterar status:", erro);
            mostrarMensagem(
                mensagemStatus,
                erro.message || "Não foi possível alterar o status.",
                "erro"
            );
        } finally {
            botaoConfirmarStatus.disabled = false;
            botaoConfirmarStatus.textContent = "Salvar status";
        }
    }

    async function excluirVaga() {
        if (!exigirAdministrador() || !vagaParaExcluir) return;

        const vaga = vagaParaExcluir;
        const id = obterId(vaga);

        botaoConfirmarExclusao.disabled = true;
        botaoConfirmarExclusao.textContent = "Excluindo...";
        mostrarMensagem(mensagemExclusao, "");

        try {
            await requisicaoAPI(`${API_VAGAS}/${encodeURIComponent(id)}`, {
                method: "DELETE"
            });

            vagaParaExcluir = null;
            fecharModal(modalExclusao);

            mostrarMensagem(
                mensagemLista,
                `Vaga ${obterCodigo(vaga)} excluída com sucesso.`,
                "sucesso"
            );

            await carregarVagas();
        } catch (erro) {
            console.error("Erro ao excluir vaga:", erro);
            mostrarMensagem(
                mensagemExclusao,
                erro.message || "Não foi possível excluir a vaga.",
                "erro"
            );
        } finally {
            botaoConfirmarExclusao.disabled = false;
            botaoConfirmarExclusao.textContent = "Excluir vaga";
        }
    }

    function configurarTema() {
        let temaSalvo = null;

        try {
            temaSalvo = localStorage.getItem("tema-estacionamento");
        } catch {}

        if (temaSalvo === "claro") {
            document.body.classList.replace("tema-escuro", "tema-claro");
        }

        atualizarBotaoTema();
    }

    function atualizarBotaoTema() {
        if (!botaoTema) return;

        const claro = document.body.classList.contains("tema-claro");

        botaoTema.textContent = claro ? "☾ Modo escuro" : "☀ Modo claro";
        botaoTema.setAttribute(
            "aria-label",
            claro ? "Ativar modo escuro" : "Ativar modo claro"
        );

        elemento("theme-color")?.setAttribute(
            "content",
            claro ? "#f4f1f8" : "#11131a"
        );
    }

    botaoNovaVaga?.addEventListener("click", () => {
        if (exigirAdministrador()) abrirFormulario();
    });

    formularioVaga?.addEventListener("submit", salvarVaga);
    formularioStatus?.addEventListener("submit", salvarStatus);
    botaoConfirmarExclusao?.addEventListener("click", excluirVaga);
    campoPesquisa.addEventListener("input", renderizarVagas);

    document.querySelectorAll("[data-fechar-modal]").forEach(botao => {
        botao.addEventListener("click", () => {
            const modal = botao.closest(".fundo-modal");
            fecharModal(modal);

            if (modal === modalExclusao) vagaParaExcluir = null;
        });
    });

    [modalVaga, modalStatus, modalExclusao].filter(Boolean).forEach(modal => {
        modal.addEventListener("click", evento => {
            if (evento.target === modal) {
                fecharModal(modal);
                if (modal === modalExclusao) vagaParaExcluir = null;
            }
        });
    });

    document.addEventListener("keydown", evento => {
        if (evento.key !== "Escape") return;

        const modalAberto = [modalVaga, modalStatus, modalExclusao]
            .filter(Boolean)
            .find(modal => !modal.hidden);

        if (modalAberto) {
            fecharModal(modalAberto);
            if (modalAberto === modalExclusao) vagaParaExcluir = null;
        }
    });

    botaoTema?.addEventListener("click", () => {
        const ficandoClaro = !document.body.classList.contains("tema-claro");

        document.body.classList.toggle("tema-claro", ficandoClaro);
        document.body.classList.toggle("tema-escuro", !ficandoClaro);

        try {
            localStorage.setItem(
                "tema-estacionamento",
                ficandoClaro ? "claro" : "escuro"
            );
        } catch {}

        atualizarBotaoTema();
    });

    configurarTema();
    carregarVagas();
});
