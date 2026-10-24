
"use strict";

const API_CLIENTES = "/api/clientes";

document.addEventListener("DOMContentLoaded", () => {
    const perfil = (
        document.body.dataset.perfil || ""
    ).trim().toUpperCase();

    const ehAdmin = perfil === "ADMINISTRADOR";
    const ehOperador = perfil === "OPERADOR";
    const podeCadastrar = ehAdmin || ehOperador;

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

    const mensagemFormulario = document.getElementById(
        "mensagem-formulario-cliente"
    );

    const mensagemLista = document.getElementById(
        "mensagem-lista-clientes"
    );

    let clientes = [];
    let carregando = false;

    if (!listaClientes) {
        console.error("A tabela de clientes não foi encontrada.");
        return;
    }

    // Valida se os elementos necessários ao cadastro estão presentes.
    if (podeCadastrar && (
        !formulario ||
        !painelFormulario ||
        !campoId ||
        !campoNome ||
        !campoDocumento ||
        !campoEmail ||
        !botaoNovo ||
        !botaoCancelar ||
        !botaoSalvar ||
        !tituloFormulario
    )) {
        console.error("O formulário de clientes está incompleto.");
        return;
    }

    function mostrarMensagem(elemento, texto, tipo = "") {
        if (!elemento) return;

        elemento.textContent = texto;
        elemento.classList.remove("erro", "sucesso");

        if (tipo) {
            elemento.classList.add(tipo);
        }
    }

    async function requisicaoAPI(url, opcoes = {}) {
        const resposta = await fetch(url, {
            credentials: "same-origin",
            ...opcoes,
            headers: {
                ...(opcoes.body
                    ? { "Content-Type": "application/json" }
                    : {}),
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
            const detalhe =
                dados?.detail ||
                dados?.mensagem ||
                `Erro HTTP ${resposta.status}.`;

            const mensagem = Array.isArray(detalhe)
                ? detalhe.map(item => item.msg || String(item)).join(", ")
                : String(detalhe);

            throw new Error(mensagem);
        }

        return dados;
    }

    function obterId(cliente) {
        return cliente.id_clients ??
            cliente.id_cliente ??
            cliente.id;
    }

    function obterNome(cliente) {
        return cliente.nome_completo ??
            cliente.nome ??
            "";
    }

    function obterDocumento(cliente) {
        return cliente.documento ?? "";
    }

    function obterEmail(cliente) {
        return cliente.email ?? "";
    }

    function clienteAtivo(cliente) {
        return cliente.ativo === undefined ||
            cliente.ativo === null ||
            cliente.ativo === true ||
            cliente.ativo === 1;
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
        const pesquisa = (campoPesquisa?.value || "")
            .trim()
            .toLocaleLowerCase("pt-BR");

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

            celula.colSpan = ehAdmin ? 5 : 4;
            celula.className = "mensagem-vazia";

            icone.className = "mensagem-vazia-icone";
            icone.setAttribute("aria-hidden", "true");
            icone.textContent = "♙";

            titulo.textContent = pesquisa
                ? "Nenhum cliente encontrado"
                : "Nenhum cliente cadastrado";

            descricao.textContent = pesquisa
                ? "Tente pesquisar usando outros termos."
                : "Ainda não há clientes cadastrados.";

            celula.append(icone, titulo, descricao);
            linha.appendChild(celula);
            listaClientes.appendChild(linha);

            return;
        }

        filtrados.forEach(cliente => {
            const linha = document.createElement("tr");

            linha.appendChild(criarCelula(obterNome(cliente)));
            linha.appendChild(criarCelula(obterDocumento(cliente)));
            linha.appendChild(criarCelula(obterEmail(cliente)));

            const celulaSituacao = document.createElement("td");
            const etiqueta = document.createElement("span");
            const ativo = clienteAtivo(cliente);

            etiqueta.className =
                `situacao-cliente${ativo ? "" : " inativo"}`;

            etiqueta.textContent = ativo ? "Ativo" : "Inativo";

            celulaSituacao.appendChild(etiqueta);
            linha.appendChild(celulaSituacao);

            // Editar e desativar continuam exclusivos do administrador.
            if (ehAdmin) {
                const celulaAcoes = document.createElement("td");
                const acoes = document.createElement("div");
                const id = obterId(cliente);

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
            }

            listaClientes.appendChild(linha);
        });
    }

    async function carregarClientes() {
        if (carregando) return;

        carregando = true;

        const linhaCarregamento = document.createElement("tr");
        const celulaCarregamento = document.createElement("td");
        const textoCarregamento = document.createElement("strong");

        celulaCarregamento.colSpan = ehAdmin ? 5 : 4;
        celulaCarregamento.className = "mensagem-vazia";
        textoCarregamento.textContent = "Carregando clientes...";

        celulaCarregamento.appendChild(textoCarregamento);
        linhaCarregamento.appendChild(celulaCarregamento);
        listaClientes.replaceChildren(linhaCarregamento);

        mostrarMensagem(mensagemLista, "");

        try {
            const dados = await requisicaoAPI(API_CLIENTES);

            if (Array.isArray(dados)) {
                clientes = dados;
            } else if (Array.isArray(dados?.clientes)) {
                clientes = dados.clientes;
            } else if (Array.isArray(dados?.items)) {
                clientes = dados.items;
            } else {
                throw new Error(
                    "A resposta da API não contém uma lista de clientes reconhecida."
                );
            }

            renderizarClientes();
        } catch (erro) {
            console.error("Erro ao carregar clientes:", erro);

            const linhaErro = document.createElement("tr");
            const celulaErro = document.createElement("td");
            const tituloErro = document.createElement("strong");
            const detalheErro = document.createElement("span");

            celulaErro.colSpan = ehAdmin ? 5 : 4;
            celulaErro.className = "mensagem-vazia";

            tituloErro.textContent =
                "Não foi possível carregar os clientes.";

            detalheErro.textContent = erro.message;

            celulaErro.append(tituloErro, detalheErro);
            linhaErro.appendChild(celulaErro);
            listaClientes.replaceChildren(linhaErro);

            mostrarMensagem(mensagemLista, erro.message, "erro");
        } finally {
            carregando = false;
        }
    }

    function abrirFormulario(cliente = null) {
        if (!podeCadastrar || !formulario || !painelFormulario) return;

        formulario.reset();
        campoId.value = cliente
            ? String(obterId(cliente) ?? "")
            : "";

        if (cliente) {
            // A edição continua restrita ao administrador.
            if (!ehAdmin) return;

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

        painelFormulario.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    function fecharFormulario() {
        if (!podeCadastrar || !formulario || !painelFormulario) return;

        formulario.reset();
        campoId.value = "";
        painelFormulario.hidden = true;

        tituloFormulario.textContent = "Cadastrar cliente";
        botaoSalvar.textContent = "Salvar cliente";

        mostrarMensagem(mensagemFormulario, "");
    }

    function editarCliente(id) {
        if (!ehAdmin) return;

        const cliente = clientes.find(
            item => String(obterId(item)) === String(id)
        );

        if (!cliente) {
            mostrarMensagem(
                mensagemLista,
                "O cliente selecionado não foi encontrado.",
                "erro"
            );
            return;
        }

        abrirFormulario(cliente);
    }

    async function salvarCliente(evento) {
        if (!podeCadastrar) return;

        evento.preventDefault();

        const nome = campoNome.value.trim();
        const documento = campoDocumento.value.trim();
        const email = campoEmail.value.trim();
        const id = campoId.value.trim();

        // Impede o operador de enviar uma atualização de cliente.
        if (!ehAdmin && id) {
            mostrarMensagem(
                mensagemFormulario,
                "O operador pode cadastrar clientes, mas não editá-los.",
                "erro"
            );
            return;
        }

        if (!nome || !documento) {
            mostrarMensagem(
                mensagemFormulario,
                "Preencha o nome completo e o documento.",
                "erro"
            );
            return;
        }

        const dados = {
            nome_completo: nome,
            documento,
            email: email || null
        };

        const editando = Boolean(id);
        const url = editando
            ? `${API_CLIENTES}/${encodeURIComponent(id)}`
            : API_CLIENTES;

        botaoSalvar.disabled = true;
        botaoSalvar.textContent = editando
            ? "Salvando..."
            : "Cadastrando...";

        mostrarMensagem(mensagemFormulario, "");

        try {
            await requisicaoAPI(url, {
                method: editando ? "PUT" : "POST",
                body: JSON.stringify(dados)
            });

            fecharFormulario();

            mostrarMensagem(
                mensagemLista,
                editando
                    ? "Cliente atualizado com sucesso."
                    : "Cliente cadastrado com sucesso.",
                "sucesso"
            );

            await carregarClientes();
        } catch (erro) {
            console.error("Erro ao salvar cliente:", erro);

            mostrarMensagem(
                mensagemFormulario,
                erro.message || "Não foi possível salvar o cliente.",
                "erro"
            );
        } finally {
            botaoSalvar.disabled = false;
            botaoSalvar.textContent = campoId.value
                ? "Salvar alterações"
                : "Salvar cliente";
        }
    }

    async function desativarCliente(id) {
        if (!ehAdmin) return;

        const cliente = clientes.find(
            item => String(obterId(item)) === String(id)
        );

        if (!cliente) {
            mostrarMensagem(
                mensagemLista,
                "O cliente selecionado não foi encontrado.",
                "erro"
            );
            return;
        }

        const confirmado = window.confirm(
            `Deseja realmente desativar o cliente "${obterNome(cliente)}"?`
        );

        if (!confirmado) return;

        mostrarMensagem(mensagemLista, "");

        try {
            await requisicaoAPI(
                `${API_CLIENTES}/${encodeURIComponent(id)}`,
                { method: "DELETE" }
            );

            mostrarMensagem(
                mensagemLista,
                "Cliente desativado com sucesso.",
                "sucesso"
            );

            await carregarClientes();
        } catch (erro) {
            console.error("Erro ao desativar cliente:", erro);

            mostrarMensagem(
                mensagemLista,
                erro.message || "Não foi possível desativar o cliente.",
                "erro"
            );
        }
    }

    // Administrador e operador podem abrir, cancelar e cadastrar.
    if (podeCadastrar && formulario) {
        botaoNovo?.addEventListener("click", () => abrirFormulario());
        botaoCancelar?.addEventListener("click", fecharFormulario);
        formulario.addEventListener("submit", salvarCliente);
    }

    // A pesquisa funciona para os dois perfis.
    campoPesquisa?.addEventListener("input", renderizarClientes);

    // A listagem é carregada para os dois perfis.
    carregarClientes();
});
