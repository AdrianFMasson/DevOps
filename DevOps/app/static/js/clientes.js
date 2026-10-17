"use strict";

const API_CLIENTES = "/api/clientes";

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("formulario-cliente");
    const painelFormulario = document.getElementById("painel-formulario-cliente");
    const botaoNovo = document.getElementById("botao-novo-cliente");
    const botaoCancelar = document.getElementById("botao-cancelar-cliente");
    const botaoSalvar = document.getElementById("botao-salvar-cliente");
    const tituloFormulario = document.getElementById("titulo-formulario-cliente");
    const campoId = document.getElementById("id-cliente");
    const campoNome = document.getElementById("nome-completo");
    const campoDocumento = document.getElementById("documento");
    const campoEmail = document.getElementById("email-cliente");
    const campoPesquisa = document.getElementById("pesquisa-clientes");
    const listaClientes = document.getElementById("lista-clientes");
    const mensagemFormulario = document.getElementById("mensagem-formulario-cliente");
    const mensagemLista = document.getElementById("mensagem-lista-clientes");

    let clientes = [];
    let carregando = false;

    if (!formulario || !painelFormulario || !listaClientes) {
        console.error("Os elementos HTML necessários para a página de clientes não foram encontrados.");
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

    function obterId(cliente) {
        return cliente.id_clients ?? cliente.id_cliente ?? cliente.id;
    }

    function obterNome(cliente) {
        return cliente.nome_completo ?? cliente.nome ?? "";
    }

    function obterDocumento(cliente) {
        return cliente.documento ?? "";
    }

    function obterEmail(cliente) {
        return cliente.email ?? "";
    }

    function clienteAtivo(cliente) {
        return cliente.ativo === true || cliente.ativo === 1;
    }

    function criarCelula(texto) {
        const celula = document.createElement("td");
        celula.textContent = texto || "—";
        return celula;
    }

    function criarBotaoAcao(texto, classe, acao, id, rotulo) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = `botao-acao-cliente ${classe}`.trim();
        botao.textContent = texto;
        botao.setAttribute("aria-label", rotulo);
        botao.addEventListener("click", () => acao(id));
        return botao;
    }

    function renderizarClientes() {
        const pesquisa = (campoPesquisa?.value || "").trim().toLocaleLowerCase("pt-BR");

        const filtrados = clientes.filter(cliente => {
            const conteudo = [
                obterNome(cliente),
                obterDocumento(cliente),
                obterEmail(cliente)
            ].join(" ").toLocaleLowerCase("pt-BR");

            return conteudo.includes(pesquisa);
        });

        listaClientes.replaceChildren();

        if (filtrados.length === 0) {
            const linha = document.createElement("tr");
            const celula = document.createElement("td");
            const icone = document.createElement("span");
            const titulo = document.createElement("strong");
            const descricao = document.createElement("span");

            celula.colSpan = 5;
            celula.className = "mensagem-vazia";
            icone.className = "mensagem-vazia-icone";
            icone.setAttribute("aria-hidden", "true");
            icone.textContent = "♙";
            titulo.textContent = pesquisa ? "Nenhum cliente encontrado" : "Nenhum cliente cadastrado";
            descricao.textContent = pesquisa ? "Tente pesquisar usando outros termos." : "Clique em “Novo cliente” para cadastrar o primeiro.";

            celula.append(icone, titulo, descricao);
            linha.appendChild(celula);
            listaClientes.appendChild(linha);
            return;
        }

        filtrados.forEach(cliente => {
            const linha = document.createElement("tr");
            const id = obterId(cliente);

            linha.appendChild(criarCelula(obterNome(cliente)));
            linha.appendChild(criarCelula(obterDocumento(cliente)));
            linha.appendChild(criarCelula(obterEmail(cliente)));

            const celulaSituacao = document.createElement("td");
            const etiqueta = document.createElement("span");
            const ativo = clienteAtivo(cliente);

            etiqueta.className = `situacao-cliente${ativo ? "" : " inativo"}`;
            etiqueta.textContent = ativo ? "Ativo" : "Inativo";
            celulaSituacao.appendChild(etiqueta);
            linha.appendChild(celulaSituacao);

            const celulaAcoes = document.createElement("td");
            const acoes = document.createElement("div");
            acoes.className = "acoes-cliente";

            acoes.appendChild(criarBotaoAcao(
                "Editar",
                "",
                editarCliente,
                id,
                `Editar cliente ${obterNome(cliente)}`
            ));

            if (ativo) {
                acoes.appendChild(criarBotaoAcao(
                    "Desativar",
                    "excluir",
                    desativarCliente,
                    id,
                    `Desativar cliente ${obterNome(cliente)}`
                ));
            }

            celulaAcoes.appendChild(acoes);
            linha.appendChild(celulaAcoes);
            listaClientes.appendChild(linha);
        });
    }

    async function carregarClientes() {
        if (carregando) return;

        carregando = true;
        listaClientes.innerHTML = `
            <tr>
                <td colspan="5" class="mensagem-vazia">
                    <strong>Carregando clientes...</strong>
                    <span>Aguarde enquanto consultamos os cadastros.</span>
                </td>
            </tr>
        `;
        mostrarMensagem(mensagemLista, "");

        try {
            const dados = await requisicaoAPI(API_CLIENTES);
            clientes = Array.isArray(dados) ? dados : dados?.clientes ?? dados?.items ?? [];

            if (!Array.isArray(clientes)) {
                throw new Error("A API não retornou uma lista válida de clientes.");
            }

            renderizarClientes();
        } catch (erro) {
            console.error("Erro ao carregar clientes:", erro);
            listaClientes.innerHTML = `
                <tr>
                    <td colspan="5" class="mensagem-vazia">
                        <strong>Não foi possível carregar os clientes.</strong>
                        <span>Verifique a conexão com o servidor e tente novamente.</span>
                    </td>
                </tr>
            `;
            mostrarMensagem(mensagemLista, erro.message, "erro");
        } finally {
            carregando = false;
        }
    }

    function abrirFormulario(cliente = null) {
        formulario.reset();
        campoId.value = cliente ? String(obterId(cliente) ?? "") : "";

        if (cliente) {
            campoNome.value = obterNome(cliente);
            campoDocumento.value = obterDocumento(cliente);
            campoEmail.value = obterEmail(cliente);
            tituloFormulario.textContent = "Editar cliente";
            botaoSalvar.textContent = "Salvar alterações";
        } else {
            tituloFormulario.textContent = "Cadastrar cliente";
            botaoSalvar.textContent = "Salvar cliente";
        }

        mostrarMensagem(mensagemFormulario, "");
        painelFormulario.hidden = false;
        campoNome.focus();
        painelFormulario.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function fecharFormulario() {
        formulario.reset();
        campoId.value = "";
        painelFormulario.hidden = true;
        mostrarMensagem(mensagemFormulario, "");
    }

    function editarCliente(id) {
        const cliente = clientes.find(item => String(obterId(item)) === String(id));

        if (!cliente) {
            mostrarMensagem(mensagemLista, "O cliente selecionado não foi encontrado.", "erro");
            return;
        }

        abrirFormulario(cliente);
    }

    async function salvarCliente(evento) {
        evento.preventDefault();

        const nome = campoNome.value.trim();
        const documento = campoDocumento.value.trim();
        const email = campoEmail.value.trim();
        const id = campoId.value.trim();

        if (!nome || !documento) {
            mostrarMensagem(mensagemFormulario, "Preencha o nome completo e o documento.", "erro");
            return;
        }

        const dados = {
            nome_completo: nome,
            documento,
            email: email || null
        };

        const editando = Boolean(id);
        const url = editando ? `${API_CLIENTES}/${encodeURIComponent(id)}` : API_CLIENTES;

        botaoSalvar.disabled = true;
        botaoSalvar.textContent = editando ? "Salvando..." : "Cadastrando...";
        mostrarMensagem(mensagemFormulario, "");

        try {
            await requisicaoAPI(url, {
                method: editando ? "PUT" : "POST",
                body: JSON.stringify(dados)
            });

            fecharFormulario();
            mostrarMensagem(
                mensagemLista,
                editando ? "Cliente atualizado com sucesso." : "Cliente cadastrado com sucesso.",
                "sucesso"
            );

            await carregarClientes();
        } catch (erro) {
            console.error("Erro ao salvar cliente:", erro);
            mostrarMensagem(mensagemFormulario, erro.message || "Não foi possível salvar o cliente.", "erro");
        } finally {
            botaoSalvar.disabled = false;
            botaoSalvar.textContent = campoId.value ? "Salvar alterações" : "Salvar cliente";
        }
    }

    async function desativarCliente(id) {
        const cliente = clientes.find(item => String(obterId(item)) === String(id));

        if (!cliente) {
            mostrarMensagem(mensagemLista, "O cliente selecionado não foi encontrado.", "erro");
            return;
        }

        const confirmado = window.confirm(
            `Deseja realmente desativar o cliente "${obterNome(cliente)}"?`
        );

        if (!confirmado) return;

        mostrarMensagem(mensagemLista, "");

        try {
            await requisicaoAPI(`${API_CLIENTES}/${encodeURIComponent(id)}`, {
                method: "DELETE"
            });

            mostrarMensagem(mensagemLista, "Cliente desativado com sucesso.", "sucesso");
            await carregarClientes();
        } catch (erro) {
            console.error("Erro ao desativar cliente:", erro);
            mostrarMensagem(mensagemLista, erro.message || "Não foi possível desativar o cliente.", "erro");
        }
    }

    botaoNovo?.addEventListener("click", () => abrirFormulario());
    botaoCancelar?.addEventListener("click", fecharFormulario);
    formulario.addEventListener("submit", salvarCliente);
    campoPesquisa?.addEventListener("input", renderizarClientes);

    carregarClientes();
});