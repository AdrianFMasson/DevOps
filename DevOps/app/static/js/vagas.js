"use strict";

const API_VAGAS = "/api/vagas";
const TIPOS_VAGA = { MENSALISTA: "Mensalista", ROTATIVA: "Rotativa" };
const STATUS_VAGA = { ATIVA: "Ativa", BLOQUEADA: "Bloqueada", INATIVA: "Inativa" };

document.addEventListener("DOMContentLoaded", () => {
    const listaVagas = document.getElementById("lista-vagas");
    const campoPesquisa = document.getElementById("pesquisa-vagas");
    const mensagemLista = document.getElementById("mensagem-lista-vagas");
    const modalVaga = document.getElementById("modal-vaga");
    const formularioVaga = document.getElementById("formulario-vaga");
    const tituloModalVaga = document.getElementById("titulo-modal-vaga");
    const descricaoModalVaga = document.getElementById("descricao-modal-vaga");
    const campoId = document.getElementById("id-vaga");
    const campoCodigo = document.getElementById("codigo-vaga");
    const campoTipo = document.getElementById("tipo-vaga");
    const campoStatus = document.getElementById("status-vaga");
    const mensagemFormulario = document.getElementById("mensagem-formulario-vaga");
    const botaoSalvar = document.getElementById("botao-salvar-vaga");
    const modalStatus = document.getElementById("modal-status-vaga");
    const formularioStatus = document.getElementById("formulario-status-vaga");
    const campoIdStatus = document.getElementById("id-status-vaga");
    const campoNovoStatus = document.getElementById("novo-status-vaga");
    const mensagemStatus = document.getElementById("mensagem-status-vaga");
    const botaoConfirmarStatus = document.getElementById("botao-confirmar-status");
    const modalExclusao = document.getElementById("modal-exclusao-vaga");
    const textoExclusao = document.getElementById("texto-exclusao-vaga");
    const mensagemExclusao = document.getElementById("mensagem-exclusao-vaga");
    const botaoConfirmarExclusao = document.getElementById("botao-confirmar-exclusao");
    const botaoTema = document.getElementById("botao-tema");
    let vagas = [];
    let carregando = false;
    let vagaParaExcluir = null;
    let modalAnterior = null;

    if (!listaVagas || !formularioVaga || !modalVaga) {
        console.error("Os elementos HTML necessários para a página de vagas não foram encontrados.");
        return;
    }

    function mostrarMensagem(elemento, texto, tipo = "") {
        if (!elemento) return;
        elemento.textContent = texto;
        elemento.classList.remove("erro", "sucesso");
        if (tipo) elemento.classList.add(tipo);
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
            throw new Error(Array.isArray(detalhe) ? detalhe.map(item => item.msg || String(item)).join(", ") : String(detalhe));
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
        document.getElementById("total-vagas").textContent = vagas.length;
        document.getElementById("vagas-ativas").textContent = vagas.filter(vaga => obterStatus(vaga) === "ATIVA").length;
        document.getElementById("vagas-bloqueadas").textContent = vagas.filter(vaga => obterStatus(vaga) === "BLOQUEADA").length;
        document.getElementById("vagas-inativas").textContent = vagas.filter(vaga => obterStatus(vaga) === "INATIVA").length;
    }

    function renderizarVagas() {
        const pesquisa = (campoPesquisa?.value || "").trim().toLocaleLowerCase("pt-BR");
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
            titulo.textContent = pesquisa ? "Nenhuma vaga encontrada" : "Nenhuma vaga cadastrada";
            descricao.textContent = pesquisa ? "Tente pesquisar usando outros termos." : "Clique em “Nova vaga” para cadastrar a primeira.";
            celula.append(titulo, descricao);
            linha.appendChild(celula);
            listaVagas.appendChild(linha);
            return;
        }

        filtradas.forEach(vaga => {
            const linha = document.createElement("tr");
            const id = obterId(vaga);
            linha.appendChild(criarCelula(obterCodigo(vaga), "codigo-vaga-tabela"));

            const celulaTipo = document.createElement("td");
            celulaTipo.appendChild(criarEtiqueta(
                TIPOS_VAGA[obterTipo(vaga)] || obterTipo(vaga) || "—",
                "etiqueta-tipo"
            ));
            linha.appendChild(celulaTipo);

            const celulaStatus = document.createElement("td");
            const status = obterStatus(vaga);
            celulaStatus.appendChild(criarEtiqueta(
                STATUS_VAGA[status] || status || "—",
                `etiqueta-status ${status.toLowerCase()}`
            ));
            linha.appendChild(celulaStatus);
            linha.appendChild(criarCelula(formatarData(vaga.dt_cadastro)));
            linha.appendChild(criarCelula(formatarData(vaga.dt_atualizacao)));

            const celulaAcoes = document.createElement("td");
            const acoes = document.createElement("div");
            acoes.className = "acoes-vaga";
            acoes.appendChild(criarBotao(
                "Editar",
                "",
                `Editar vaga ${obterCodigo(vaga)}`,
                editarVaga,
                id
            ));
            acoes.appendChild(criarBotao(
                "Status",
                "status",
                `Alterar status da vaga ${obterCodigo(vaga)}`,
                abrirModalStatus,
                id
            ));
            acoes.appendChild(criarBotao(
                "Excluir",
                "excluir",
                `Excluir vaga ${obterCodigo(vaga)}`,
                abrirModalExclusao,
                id
            ));
            celulaAcoes.appendChild(acoes);
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
            mostrarMensagem(mensagemLista, erro.message || "Não foi possível carregar as vagas.", "erro");
            ["total-vagas", "vagas-ativas", "vagas-bloqueadas", "vagas-inativas"].forEach(id => {
                document.getElementById(id).textContent = "—";
            });
        } finally {
            carregando = false;
        }
    }

    function abrirModal(modal) {
        modalAnterior = document.activeElement;
        modal.hidden = false;
        document.body.classList.add("modal-aberto");
        const foco = modal.querySelector("input:not([type=hidden]), select, button");
        window.setTimeout(() => foco?.focus(), 0);
    }

    function fecharModal(modal) {
        if (!modal || modal.hidden) return;
        modal.hidden = true;
        if (![modalVaga, modalStatus, modalExclusao].some(item => !item.hidden)) {
            document.body.classList.remove("modal-aberto");
        }
        modalAnterior?.focus?.();
    }

    function abrirFormulario(vaga = null) {
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
        const vaga = vagas.find(item => String(obterId(item)) === String(id));
        if (!vaga) {
            mostrarMensagem(mensagemLista, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }
        abrirFormulario(vaga);
    }

    function abrirModalStatus(id) {
        const vaga = vagas.find(item => String(obterId(item)) === String(id));
        if (!vaga) {
            mostrarMensagem(mensagemLista, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }
        formularioStatus.reset();
        campoIdStatus.value = String(obterId(vaga));
        campoNovoStatus.value = obterStatus(vaga);
        document.getElementById("descricao-status-vaga").textContent =
            `Vaga ${obterCodigo(vaga)} — status atual: ${STATUS_VAGA[obterStatus(vaga)] || obterStatus(vaga)}.`;
        mostrarMensagem(mensagemStatus, "");
        abrirModal(modalStatus);
    }

    function abrirModalExclusao(id) {
        const vaga = vagas.find(item => String(obterId(item)) === String(id));
        if (!vaga) {
            mostrarMensagem(mensagemLista, "A vaga selecionada não foi encontrada.", "erro");
            return;
        }
        vagaParaExcluir = vaga;
        textoExclusao.textContent =
            `Você está prestes a excluir a vaga ${obterCodigo(vaga)}. Se ela estiver vinculada a movimentações ou outros registros, o servidor poderá impedir a exclusão. Esta ação não poderá ser desfeita.`;
        mostrarMensagem(mensagemExclusao, "");
        botaoConfirmarExclusao.disabled = false;
        abrirModal(modalExclusao);
    }

    async function salvarVaga(evento) {
        evento.preventDefault();
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
                editando ? `${API_VAGAS}/${encodeURIComponent(id)}` : API_VAGAS,
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
            mostrarMensagem(mensagemFormulario, erro.message || "Não foi possível salvar a vaga.", "erro");
        } finally {
            botaoSalvar.disabled = false;
            botaoSalvar.textContent = campoId.value ? "Salvar alterações" : "Cadastrar vaga";
        }
    }

    async function salvarStatus(evento) {
        evento.preventDefault();
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
            mostrarMensagem(mensagemStatus, erro.message || "Não foi possível alterar o status.", "erro");
        } finally {
            botaoConfirmarStatus.disabled = false;
            botaoConfirmarStatus.textContent = "Salvar status";
        }
    }

    async function excluirVaga() {
        if (!vagaParaExcluir) return;
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
            mostrarMensagem(mensagemLista, `Vaga ${obterCodigo(vaga)} excluída com sucesso.`, "sucesso");
            await carregarVagas();
        } catch (erro) {
            console.error("Erro ao excluir vaga:", erro);
            mostrarMensagem(mensagemExclusao, erro.message || "Não foi possível excluir a vaga.", "erro");
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
        const claro = document.body.classList.contains("tema-claro");
        botaoTema.textContent = claro ? "☾ Modo escuro" : "☀ Modo claro";
        botaoTema.setAttribute("aria-label", claro ? "Ativar modo escuro" : "Ativar modo claro");
        document.querySelector('meta[name="theme-color"]')?.setAttribute(
            "content",
            claro ? "#f4f1f8" : "#11131a"
        );
    }

    document.getElementById("botao-nova-vaga")?.addEventListener("click", () => abrirFormulario());
    formularioVaga.addEventListener("submit", salvarVaga);
    formularioStatus.addEventListener("submit", salvarStatus);
    botaoConfirmarExclusao.addEventListener("click", excluirVaga);
    campoPesquisa?.addEventListener("input", renderizarVagas);

    document.querySelectorAll("[data-fechar-modal]").forEach(botao => {
        botao.addEventListener("click", () => {
            const modal = botao.closest(".fundo-modal");
            fecharModal(modal);
            if (modal === modalExclusao) vagaParaExcluir = null;
        });
    });

    [modalVaga, modalStatus, modalExclusao].forEach(modal => {
        modal.addEventListener("click", evento => {
            if (evento.target === modal) {
                fecharModal(modal);
                if (modal === modalExclusao) vagaParaExcluir = null;
            }
        });
    });

    document.addEventListener("keydown", evento => {
        if (evento.key !== "Escape") return;
        const modalAberto = [modalVaga, modalStatus, modalExclusao].find(modal => !modal.hidden);
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
            localStorage.setItem("tema-estacionamento", ficandoClaro ? "claro" : "escuro");
        } catch {}
        atualizarBotaoTema();
    });

    configurarTema();
    carregarVagas();
});