
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
    const campoTelefone = document.getElementById("telefone-cliente");

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

    if (
        podeCadastrar &&
        (
            !formulario ||
            !painelFormulario ||
            !campoId ||
            !campoNome ||
            !campoDocumento ||
            !campoEmail ||
            !campoTelefone ||
            !botaoNovo ||
            !botaoCancelar ||
            !botaoSalvar ||
            !tituloFormulario
        )
    ) {
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

    function obterTelefone(cliente) {
        return cliente.telefone ?? "";
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
                obterEmail(cliente),
                obterTelefone(cliente)
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

        // Verifica a permissão antes de preencher ou abrir a edição.
        if (cliente && !ehAdmin) return;

        formulario.reset();

        campoId.value = cliente
            ? String(obterId(cliente) ?? "")
            : "";

        if (cliente) {
            campoNome.value = obterNome(cliente);
            campoDocumento.value = obterDocumento(cliente);
            campoEmail.value = obterEmail(cliente);
            campoTelefone.value = obterTelefone(cliente);

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
        const telefone = campoTelefone.value.trim();
        const id = campoId.value.trim();

        // Operador não pode editar clientes.
        if (!ehAdmin && id) {
            mostrarMensagem(
                mensagemFormulario,
                "O operador pode cadastrar clientes, mas não editá-los.",
                "erro"
            );
            return;
        }

        // Todos os campos são obrigatórios.
        if (!nome || !documento || !email || !telefone) {
            mostrarMensagem(
                mensagemFormulario,
                "Preencha todos os campos antes de salvar o cliente.",
                "erro"
            );
            return;
        }

        // Não permite números no nome.
        if (/\d/.test(nome)) {
            mostrarMensagem(
                mensagemFormulario,
                "O nome não pode conter números.",
                "erro"
            );
            campoNome.focus();
            return;
        }

        // Exige 11 dígitos no CPF.
        const cpfNumeros = documento.replace(/\D/g, "");

        if (cpfNumeros.length !== 11) {
            mostrarMensagem(
                mensagemFormulario,
                "Informe um CPF com 11 dígitos.",
                "erro"
            );
            campoDocumento.focus();
            return;
        }

        // Verifica o formato básico do e-mail.
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            mostrarMensagem(
                mensagemFormulario,
                "Informe um e-mail válido.",
                "erro"
            );
            campoEmail.focus();
            return;
        }

        // Exige pelo menos 10 dígitos no telefone.
        const telefoneNumeros = telefone.replace(/\D/g, "");

        if (telefoneNumeros.length < 10 || telefoneNumeros.length > 13) {
            mostrarMensagem(
                mensagemFormulario,
                "Informe um telefone válido, com DDD.",
                "erro"
            );
            campoTelefone.focus();
            return;
        }

        const dados = {
            nome_completo: nome,
            documento,
            email,
            telefone
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

    // Impede números no nome enquanto o usuário digita.
    campoNome?.addEventListener("input", function () {
        this.value = this.value.replace(/[0-9]/g, "");
    });

    // Formata o CPF automaticamente: 000.000.000-00.
    campoDocumento?.addEventListener("input", function () {
        let cpf = this.value.replace(/\D/g, "").substring(0, 11);

        if (cpf.length > 9) {
            cpf = cpf.replace(
                /^(\d{3})(\d{3})(\d{3})(\d{1,2}).*/,
                "$1.$2.$3-$4"
            );
        } else if (cpf.length > 6) {
            cpf = cpf.replace(
                /^(\d{3})(\d{3})(\d{1,3}).*/,
                "$1.$2.$3"
            );
        } else if (cpf.length > 3) {
            cpf = cpf.replace(
                /^(\d{3})(\d{1,3}).*/,
                "$1.$2"
            );
        }

        this.value = cpf;
    });

    // Formata o telefone enquanto o usuário digita.
    campoTelefone?.addEventListener("input", function () {
        let numeros = this.value.replace(/\D/g, "").substring(0, 11);

        if (numeros.length > 10) {
            numeros = numeros.replace(
                /^(\d{2})(\d{5})(\d{1,4}).*/,
                "($1) $2-$3"
            );
        } else if (numeros.length > 6) {
            numeros = numeros.replace(
                /^(\d{2})(\d{4})(\d{1,4}).*/,
                "($1) $2-$3"
            );
        } else if (numeros.length > 2) {
            numeros = numeros.replace(
                /^(\d{2})(\d{1,5})/,
                "($1) $2"
            );
        } else if (numeros.length > 0) {
            numeros = numeros.replace(/^(\d{1,2})/, "($1");
        }

        this.value = numeros;
    });

    // Administrador e operador podem abrir, cancelar e cadastrar.
    if (podeCadastrar && formulario) {
        botaoNovo?.addEventListener("click", () => abrirFormulario());
        botaoCancelar?.addEventListener("click", fecharFormulario);
        formulario.addEventListener("submit", salvarCliente);
    }

    campoPesquisa?.addEventListener("input", renderizarClientes);

    carregarClientes();
});
