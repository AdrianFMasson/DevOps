
"use strict";

document.addEventListener("DOMContentLoaded", iniciarPaginaVeiculos);

function iniciarPaginaVeiculos() {
    const API_VEICULOS = "/api/veiculos";
    const API_CLIENTES = "/api/clientes";
    const API_MARCAS = "/api/marcas-veiculo";
    const API_MODELOS = "/api/modelos-veiculo";
    const API_VINCULOS = "/api/vagas-mensalistas";
    const API_VAGAS = "/api/vagas";

    const elemento = id => document.getElementById(id);

    // Identifica o perfil informado pelo template Jinja2.
    const perfilUsuario = (
        document.body.dataset.perfil || ""
    ).trim().toUpperCase();

    const ehAdministrador =
        perfilUsuario === "ADMINISTRADOR";

    const painelFormulario =
        elemento("painel-formulario-veiculo");

    const formulario =
        elemento("formulario-veiculo");

    const lista =
        elemento("lista-veiculos");

    const pesquisa =
        elemento("pesquisa-veiculos");

    const botaoNovoVeiculo =
        elemento("botao-novo-veiculo");

    const botaoCancelar =
        elemento("botao-cancelar-veiculo");

    const campoId =
        elemento("id-veiculo");

    const campoPlaca =
        elemento("placa-veiculo");

    const campoCor =
        elemento("cor-veiculo");

    const campoMarca =
        elemento("marca-veiculo");

    const campoModelo =
        elemento("modelo-veiculo");

    const campoCliente =
        elemento("cliente-veiculo");

    const campoMensalista =
        elemento("mensalista-veiculo");

    const tituloFormulario =
        elemento("titulo-formulario-veiculo");

    const mensagemFormulario =
        elemento("mensagem-formulario-veiculo");

    const mensagemLista =
        elemento("mensagem-lista-veiculos");

    const botaoSalvar =
        elemento("botao-salvar-veiculo");

    let veiculos = [];
    let marcas = [];
    let modelos = [];
    let clientes = [];
    let vinculosMensalistas = [];
    let vagasMensalistas = [];

    let mensalistaOriginal = false;

    // O operador não pode utilizar o formulário.
    if (!ehAdministrador) {
        if (botaoNovoVeiculo) {
            botaoNovoVeiculo.hidden = true;
        }

        if (painelFormulario) {
            painelFormulario.hidden = true;
        }
    }

    // --------------------------------------------------
    // REQUISIÇÕES À API
    // --------------------------------------------------

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
            let detalhe =
                dados?.detail ||
                dados?.mensagem ||
                `Erro HTTP ${resposta.status}.`;

            if (Array.isArray(detalhe)) {
                detalhe = detalhe
                    .map(item => item.msg || String(item))
                    .join(", ");
            }

            throw new Error(String(detalhe));
        }

        return dados;
    }

    function obterLista(dados, propriedade) {
        if (Array.isArray(dados)) {
            return dados;
        }

        if (Array.isArray(dados?.[propriedade])) {
            return dados[propriedade];
        }

        if (Array.isArray(dados?.items)) {
            return dados.items;
        }

        if (Array.isArray(dados?.results)) {
            return dados.results;
        }

        return [];
    }

    // --------------------------------------------------
    // CLIENTES, MARCAS E MODELOS
    // --------------------------------------------------

    function idCliente(cliente) {
        return cliente?.id_clients ??
            cliente?.id_cliente ??
            cliente?.id;
    }

    function nomeCliente(cliente) {
        return cliente?.nome_completo ??
            cliente?.nome_cliente ??
            cliente?.nome ??
            "—";
    }

    function idModeloVeiculo(veiculo) {
        return veiculo.id_modelo ??
            veiculo.id_modelo_veiculo ??
            veiculo.modelo_id ??
            veiculo.modelo?.id_modelo ??
            veiculo.modelo?.id;
    }

    function obterModelo(veiculo) {
        if (
            veiculo.modelo &&
            typeof veiculo.modelo === "object"
        ) {
            return veiculo.modelo;
        }

        const id = idModeloVeiculo(veiculo);

        return modelos.find(modelo =>
            String(modelo.id_modelo ?? modelo.id) === String(id)
        );
    }

    function obterMarca(veiculo) {
        const modelo = obterModelo(veiculo);

        if (
            modelo?.marca &&
            typeof modelo.marca === "object"
        ) {
            return modelo.marca;
        }

        if (
            veiculo.marca &&
            typeof veiculo.marca === "object"
        ) {
            return veiculo.marca;
        }

        const id = modelo?.id_marca ??
            modelo?.id_marca_veiculo ??
            veiculo.id_marca ??
            veiculo.id_marca_veiculo ??
            veiculo.marca_id ??
            veiculo.marca?.id_marca ??
            veiculo.marca?.id;

        return marcas.find(marca =>
            String(marca.id_marca ?? marca.id) === String(id)
        );
    }

    function nomeModelo(veiculo) {
        const modelo = obterModelo(veiculo);

        return modelo?.nome_modelo ??
            modelo?.nome ??
            modelo?.descricao ??
            veiculo.nome_modelo ??
            veiculo.modelo_nome ??
            (
                typeof veiculo.modelo === "string"
                    ? veiculo.modelo
                    : null
            ) ??
            "—";
    }

    function nomeMarca(veiculo) {
        const marca = obterMarca(veiculo);

        return marca?.nome_marca ??
            marca?.nome ??
            marca?.descricao ??
            veiculo.nome_marca ??
            veiculo.marca_nome ??
            (
                typeof veiculo.marca === "string"
                    ? veiculo.marca
                    : null
            ) ??
            "—";
    }

    function idResponsavel(veiculo) {
        return veiculo.id_clients ??
            veiculo.id_cliente ??
            veiculo.cliente_id ??
            veiculo.cliente?.id_clients ??
            veiculo.cliente?.id_cliente ??
            veiculo.clients?.id_clients;
    }

    function nomeResponsavel(veiculo) {
        const id = idResponsavel(veiculo);

        const cliente = clientes.find(item =>
            String(idCliente(item)) === String(id)
        );

        if (cliente) {
            return nomeCliente(cliente);
        }

        if (
            veiculo.cliente &&
            typeof veiculo.cliente === "object"
        ) {
            return nomeCliente(veiculo.cliente);
        }

        if (
            veiculo.clients &&
            typeof veiculo.clients === "object"
        ) {
            return nomeCliente(veiculo.clients);
        }

        return veiculo.nome_cliente ?? "—";
    }

    // --------------------------------------------------
    // MENSALISTAS
    // --------------------------------------------------

    function dataHojeISO() {
        const hoje = new Date();

        return [
            hoje.getFullYear(),
            String(hoje.getMonth() + 1).padStart(2, "0"),
            String(hoje.getDate()).padStart(2, "0")
        ].join("-");
    }

    function vinculoEstaAtivo(
        vinculo,
        hoje = dataHojeISO()
    ) {
        const inicio = String(
            vinculo?.data_inicio ?? ""
        ).slice(0, 10);

        const fim =
            vinculo?.data_fim == null ||
            vinculo.data_fim === ""
                ? null
                : String(vinculo.data_fim).slice(0, 10);

        return inicio !== "" &&
            inicio <= hoje &&
            fim === null;
    }

    function obterVinculoAtivo(
        idClients,
        listaVinculos = vinculosMensalistas
    ) {
        if (idClients == null) {
            return null;
        }

        return listaVinculos.find(vinculo =>
            String(vinculo.id_clients) === String(idClients) &&
            vinculoEstaAtivo(vinculo)
        ) ?? null;
    }

    function clienteEhMensalista(idClients) {
        return obterVinculoAtivo(idClients) !== null;
    }

    async function carregarVinculosMensalistas() {
        const dados = await requisicaoAPI(
            `${API_VINCULOS}?incluir_encerrados=true`
        );

        vinculosMensalistas = obterLista(
            dados,
            "vinculos"
        );

        return vinculosMensalistas;
    }

    async function carregarVagasMensalistas() {
        const dados = await requisicaoAPI(API_VAGAS);
        const vagas = obterLista(dados, "vagas");

        vagasMensalistas = vagas.filter(vaga => {
            const tipo = String(
                vaga.tipo ?? vaga.tipo_vaga ?? ""
            ).toUpperCase();

            const statusVaga = String(
                vaga.status ?? ""
            ).toUpperCase();

            return tipo.includes("MENSALISTA") &&
                statusVaga.includes("ATIVA");
        });

        return vagasMensalistas;
    }

    // --------------------------------------------------
    // MENSAGENS E ELEMENTOS DA TABELA
    // --------------------------------------------------

    function mostrarMensagem(texto, tipo = "") {
        if (!mensagemFormulario) {
            return;
        }

        mensagemFormulario.textContent = texto;
        mensagemFormulario.className =
            "mensagem-formulario-veiculo";

        if (tipo) {
            mensagemFormulario.classList.add(tipo);
        }
    }

    function mostrarMensagemLista(texto, tipo = "") {
        if (!mensagemLista) {
            return;
        }

        mensagemLista.textContent = texto;
        mensagemLista.className =
            "mensagem-lista-veiculos";

        if (tipo) {
            mensagemLista.classList.add(tipo);
        }
    }

    function criarCelula(valor) {
        const td = document.createElement("td");

        td.textContent =
            valor == null || valor === ""
                ? "—"
                : String(valor);

        return td;
    }

    function criarSituacao(texto, classe) {
        const span = document.createElement("span");

        span.className = `situacao-veiculo ${classe}`;
        span.textContent = texto;

        return span;
    }

    function criarBotaoAcao(
        texto,
        classe,
        callback,
        veiculo
    ) {
        const botao = document.createElement("button");

        botao.type = "button";
        botao.className =
            `botao-acao-veiculo ${classe}`.trim();

        botao.textContent = texto;

        botao.addEventListener("click", () => {
            if (!ehAdministrador) {
                mostrarMensagemLista(
                    "Seu perfil permite apenas consultar veículos.",
                    "erro"
                );
                return;
            }

            callback(veiculo);
        });

        return botao;
    }

    // --------------------------------------------------
    // RENDERIZAÇÃO E PESQUISA
    // --------------------------------------------------

    function renderizarVeiculos() {
        if (!lista) {
            return;
        }

        const termo = (
            pesquisa?.value || ""
        ).trim().toLocaleLowerCase("pt-BR");

        const filtrados = veiculos.filter(veiculo => [
            veiculo.placa,
            veiculo.cor,
            nomeMarca(veiculo),
            nomeModelo(veiculo),
            nomeResponsavel(veiculo)
        ].some(valor =>
            String(valor ?? "")
                .toLocaleLowerCase("pt-BR")
                .includes(termo)
        ));

        lista.replaceChildren();

        if (filtrados.length === 0) {
            const tr = document.createElement("tr");
            const td = document.createElement("td");

            td.colSpan = 7;
            td.className = "mensagem-vazia";

            const icone = document.createElement("span");
            icone.className = "mensagem-vazia-icone";
            icone.setAttribute("aria-hidden", "true");
            icone.textContent = "🚗";

            const titulo = document.createElement("strong");
            titulo.textContent = termo
                ? "Nenhum veículo encontrado"
                : "Nenhum veículo cadastrado";

            const descricao = document.createElement("span");
            descricao.textContent = termo
                ? "Tente pesquisar por outra placa, marca ou modelo."
                : ehAdministrador
                    ? "Cadastre um veículo para começar."
                    : "Não há veículos para exibir.";

            td.append(icone, titulo, descricao);
            tr.appendChild(td);
            lista.appendChild(tr);

            return;
        }

        filtrados.forEach(veiculo => {
            const tr = document.createElement("tr");

            tr.appendChild(criarCelula(veiculo.placa));
            tr.appendChild(criarCelula(nomeMarca(veiculo)));
            tr.appendChild(criarCelula(nomeModelo(veiculo)));
            tr.appendChild(criarCelula(veiculo.cor));
            tr.appendChild(criarCelula(nomeResponsavel(veiculo)));

            const mensalista = clienteEhMensalista(
                idResponsavel(veiculo)
            );

            const tdMensalista =
                document.createElement("td");

            tdMensalista.appendChild(
                criarSituacao(
                    mensalista ? "Sim" : "Não",
                    mensalista
                        ? "mensalista"
                        : "nao-mensalista"
                )
            );

            tr.appendChild(tdMensalista);

            const tdAcoes = document.createElement("td");
            const acoes = document.createElement("div");

            acoes.className = "acoes-veiculo";

            if (ehAdministrador) {
                acoes.appendChild(
                    criarBotaoAcao(
                        "Editar",
                        "",
                        abrirEdicao,
                        veiculo
                    )
                );

                acoes.appendChild(
                    criarBotaoAcao(
                        "Excluir",
                        "excluir",
                        excluirVeiculo,
                        veiculo
                    )
                );
            } else {
                const consulta =
                    document.createElement("span");

                consulta.className =
                    "acoes-somente-consulta";

                consulta.textContent = "Somente consulta";

                acoes.appendChild(consulta);
            }

            tdAcoes.appendChild(acoes);
            tr.appendChild(tdAcoes);
            lista.appendChild(tr);
        });
    }

    // --------------------------------------------------
    // CARREGAMENTO DOS DADOS
    // --------------------------------------------------

    async function carregarTudo() {
        if (lista) {
            lista.innerHTML = `
                <tr>
                    <td colspan="7" class="mensagem-vazia">
                        <span
                            class="mensagem-vazia-icone"
                            aria-hidden="true"
                        >🚗</span>
                        <strong>Carregando veículos...</strong>
                        <span>
                            Aguarde enquanto consultamos os cadastros.
                        </span>
                    </td>
                </tr>`;
        }

        try {
            const [
                dadosVeiculos,
                dadosMarcas,
                dadosModelos,
                dadosClientes
            ] = await Promise.all([
                requisicaoAPI(API_VEICULOS),
                requisicaoAPI(API_MARCAS),
                requisicaoAPI(API_MODELOS),
                requisicaoAPI(API_CLIENTES)
            ]);

            veiculos = obterLista(
                dadosVeiculos,
                "veiculos"
            );

            marcas = obterLista(
                dadosMarcas,
                "marcas"
            );

            modelos = obterLista(
                dadosModelos,
                "modelos"
            );

            clientes = obterLista(
                dadosClientes,
                "clientes"
            );

            try {
                await carregarVinculosMensalistas();
            } catch (erro) {
                console.error(
                    "Erro ao carregar vínculos mensalistas:",
                    erro
                );

                throw new Error(
                    "Não foi possível consultar os vínculos mensalistas. " +
                    erro.message
                );
            }

            renderizarVeiculos();
            mostrarMensagemLista("");
        } catch (erro) {
            console.error(
                "Erro ao carregar veículos:",
                erro
            );

            mostrarMensagemLista(
                erro.message,
                "erro"
            );

            if (lista) {
                lista.innerHTML = `
                    <tr>
                        <td colspan="7" class="mensagem-vazia">
                            <strong>
                                Não foi possível carregar os veículos.
                            </strong>
                            <span>
                                Verifique a conexão com o servidor e tente novamente.
                            </span>
                        </td>
                    </tr>`;
            }
        }
    }

    async function carregarClientes(idSelecionado = null) {
        const dados = await requisicaoAPI(API_CLIENTES);

        clientes = obterLista(dados, "clientes");

        campoCliente.replaceChildren();

        const inicial = document.createElement("option");
        inicial.value = "";
        inicial.textContent = "Selecione o cliente";

        campoCliente.appendChild(inicial);

        clientes.forEach(cliente => {
            const id = idCliente(cliente);

            if (id == null) {
                return;
            }

            const opcao = document.createElement("option");

            opcao.value = String(id);
            opcao.textContent = nomeCliente(cliente);

            campoCliente.appendChild(opcao);
        });

        if (idSelecionado != null) {
            campoCliente.value = String(idSelecionado);

            if (
                campoCliente.value !== String(idSelecionado)
            ) {
                throw new Error(
                    `O cliente ID ${idSelecionado} não foi encontrado na lista.`
                );
            }
        }
    }

    async function carregarMarcas(idSelecionado = null) {
        const dados = await requisicaoAPI(API_MARCAS);

        marcas = obterLista(dados, "marcas");

        campoMarca.replaceChildren();

        const inicial = document.createElement("option");
        inicial.value = "";
        inicial.textContent = "Selecione a marca";

        campoMarca.appendChild(inicial);

        marcas
            .filter(marca =>
                marca.ativo !== false &&
                marca.ativo !== 0
            )
            .forEach(marca => {
                const option =
                    document.createElement("option");

                option.value =
                    marca.id_marca ?? marca.id;

                option.textContent =
                    marca.nome_marca ?? marca.nome;

                campoMarca.appendChild(option);
            });

        if (idSelecionado != null) {
            campoMarca.value = String(idSelecionado);
        }
    }

    async function carregarModelos(
        idMarca,
        idSelecionado = null
    ) {
        campoModelo.replaceChildren();

        const inicial = document.createElement("option");

        inicial.value = "";
        inicial.textContent = idMarca
            ? "Selecione o modelo"
            : "Selecione primeiro a marca";

        campoModelo.appendChild(inicial);
        campoModelo.disabled = !idMarca;

        if (!idMarca) {
            return;
        }

        const dados = await requisicaoAPI(API_MODELOS);

        modelos = obterLista(dados, "modelos");

        modelos
            .filter(modelo => {
                const idDaMarca = modelo.id_marca ??
                    modelo.id_marca_veiculo ??
                    modelo.marca_id;

                return String(idDaMarca) === String(idMarca) &&
                    modelo.ativo !== false &&
                    modelo.ativo !== 0;
            })
            .forEach(modelo => {
                const option =
                    document.createElement("option");

                option.value =
                    modelo.id_modelo ?? modelo.id;

                option.textContent =
                    modelo.nome_modelo ??
                    modelo.nome ??
                    modelo.descricao;

                campoModelo.appendChild(option);
            });

        campoModelo.disabled = false;

        if (idSelecionado != null) {
            campoModelo.value = String(idSelecionado);
        }
    }

    // --------------------------------------------------
    // CADASTRO E EDIÇÃO
    // --------------------------------------------------

    async function abrirNovoVeiculo() {
        if (!ehAdministrador) {
            return;
        }

        formulario.reset();

        campoId.value = "";
        mensalistaOriginal = false;

        tituloFormulario.textContent =
            "Cadastrar veículo";

        botaoSalvar.textContent = "Salvar veículo";

        mostrarMensagem("");

        campoModelo.disabled = true;
        painelFormulario.hidden = false;

        painelFormulario.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        try {
            await Promise.all([
                carregarClientes(),
                carregarMarcas()
            ]);

            await carregarModelos("");
        } catch (erro) {
            mostrarMensagem(
                `Erro ao carregar os dados: ${erro.message}`,
                "erro"
            );
        }
    }

    async function abrirEdicao(veiculo) {
        if (!ehAdministrador) {
            return;
        }

        mostrarMensagem("");
        formulario.reset();

        campoId.value =
            veiculo.id_veiculo ?? veiculo.id ?? "";

        campoPlaca.value = veiculo.placa ?? "";
        campoCor.value = veiculo.cor ?? "";

        const modelo = obterModelo(veiculo);
        const marca = obterMarca(veiculo);

        const idMarca = marca?.id_marca ??
            marca?.id ??
            modelo?.id_marca ??
            modelo?.id_marca_veiculo ??
            veiculo.id_marca;

        const idModelo = idModeloVeiculo(veiculo);
        const idDoCliente = idResponsavel(veiculo);

        mensalistaOriginal =
            clienteEhMensalista(idDoCliente);

        tituloFormulario.textContent = "Editar veículo";
        botaoSalvar.textContent = "Salvar alterações";

        painelFormulario.hidden = false;

        painelFormulario.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        try {
            await carregarVinculosMensalistas();

            mensalistaOriginal =
                clienteEhMensalista(idDoCliente);

            await Promise.all([
                carregarClientes(idDoCliente),
                carregarMarcas(idMarca)
            ]);

            if (idMarca != null) {
                await carregarModelos(idMarca, idModelo);
            } else {
                await carregarModelos("");
            }

            campoMensalista.value =
                mensalistaOriginal ? "sim" : "nao";
        } catch (erro) {
            console.error(
                "Erro ao abrir edição:",
                erro
            );

            mostrarMensagem(
                `Não foi possível carregar os dados para edição: ${erro.message}`,
                "erro"
            );
        }
    }

    function fecharFormulario() {
        // O operador não pode controlar o formulário.
        if (!ehAdministrador) {
            return;
        }

        if (!painelFormulario || !formulario) {
            return;
        }

        painelFormulario.hidden = true;

        formulario.reset();

        campoId.value = "";
        campoModelo.disabled = true;

        mensalistaOriginal = false;

        tituloFormulario.textContent =
            "Cadastrar veículo";

        botaoSalvar.textContent = "Salvar veículo";

        mostrarMensagem("");
    }

    // --------------------------------------------------
    // SINCRONIZAÇÃO DO VÍNCULO MENSALISTA
    // --------------------------------------------------

    async function sincronizarMensalista(
        idClients,
        desejaSerMensalista
    ) {
        if (!ehAdministrador) {
            throw new Error(
                "Seu perfil permite apenas consultar veículos."
            );
        }

        const hoje = dataHojeISO();

        if (idClients == null) {
            throw new Error(
                "Não foi possível identificar o cliente responsável."
            );
        }

        const todosVinculos =
            await carregarVinculosMensalistas();

        const vinculosCliente = todosVinculos.filter(v =>
            String(v.id_clients) === String(idClients)
        );

        const ativo = obterVinculoAtivo(
            idClients,
            vinculosCliente
        );

        if (desejaSerMensalista && ativo) {
            return;
        }

        if (!desejaSerMensalista && !ativo) {
            return;
        }

        if (!desejaSerMensalista && ativo) {
            const idVinculo =
                ativo.id_vinculo ?? ativo.id;

            if (idVinculo == null) {
                throw new Error(
                    "O vínculo mensalista ativo não possui um identificador."
                );
            }

            await requisicaoAPI(
                `${API_VINCULOS}/${encodeURIComponent(idVinculo)}` +
                `/encerrar?data_fim=${encodeURIComponent(hoje)}`,
                { method: "PATCH" }
            );

            vinculosMensalistas =
                vinculosMensalistas.map(v =>
                    String(v.id_vinculo ?? v.id) ===
                    String(idVinculo)
                        ? { ...v, data_fim: hoje }
                        : v
                );

            return;
        }

        const ocupadas = new Set(
            vinculosMensalistas
                .filter(v => vinculoEstaAtivo(v, hoje))
                .map(v => v.id_vaga)
                .filter(id => id != null)
                .map(String)
        );

        const vagas = await carregarVagasMensalistas();

        const vagaDisponivel = vagas.find(vaga => {
            const id = vaga.id_vaga ?? vaga.id;

            return id != null &&
                !ocupadas.has(String(id));
        });

        const idVaga =
            vagaDisponivel?.id_vaga ??
            vagaDisponivel?.id;

        if (idVaga == null) {
            throw new Error(
                "Não há vaga mensalista disponível para vincular este cliente. " +
                "Cadastre ou libere uma vaga mensalista ativa e tente novamente."
            );
        }

        await requisicaoAPI(API_VINCULOS, {
            method: "POST",
            body: JSON.stringify({
                id_clients: Number(idClients),
                id_vaga: Number(idVaga),
                data_inicio: hoje,
                data_fim: null
            })
        });

        await carregarVinculosMensalistas();
    }

    // --------------------------------------------------
    // SALVAR VEÍCULO
    // --------------------------------------------------

    async function salvarVeiculo(evento) {
        evento.preventDefault();

        if (!ehAdministrador) {
            mostrarMensagem(
                "Seu perfil permite apenas consultar veículos.",
                "erro"
            );
            return;
        }

        mostrarMensagem("");

        if (!formulario.reportValidity()) {
            return;
        }

        const id = campoId.value.trim();

        const idClienteSelecionado =
            Number(campoCliente.value);

        const desejaSerMensalista =
            campoMensalista.value === "sim";

        if (!idClienteSelecionado) {
            mostrarMensagem(
                "Selecione o cliente responsável.",
                "erro"
            );
            return;
        }

        if (!campoModelo.value) {
            mostrarMensagem(
                "Selecione o modelo do veículo.",
                "erro"
            );
            return;
        }

        const dados = {
            id_clients: idClienteSelecionado,
            id_modelo: Number(campoModelo.value),
            placa: campoPlaca.value.trim().toUpperCase(),
            cor: campoCor.value
        };

        botaoSalvar.disabled = true;
        botaoSalvar.textContent = "Salvando...";

        try {
            await requisicaoAPI(
                id
                    ? `${API_VEICULOS}/${encodeURIComponent(id)}`
                    : API_VEICULOS,
                {
                    method: id ? "PUT" : "POST",
                    body: JSON.stringify(dados)
                }
            );

            await sincronizarMensalista(
                idClienteSelecionado,
                desejaSerMensalista
            );

            fecharFormulario();

            await carregarTudo();

            mostrarMensagemLista(
                id
                    ? "Veículo e vínculo mensalista atualizados com sucesso."
                    : "Veículo cadastrado com sucesso.",
                "sucesso"
            );
        } catch (erro) {
            console.error(
                "Erro ao salvar veículo:",
                erro
            );

            mostrarMensagem(
                erro.message ||
                    "Não foi possível salvar os dados.",
                "erro"
            );

            try {
                await carregarTudo();
            } catch (erroAtualizacao) {
                console.error(
                    "Erro ao atualizar a lista:",
                    erroAtualizacao
                );
            }
        } finally {
            botaoSalvar.disabled = false;

            botaoSalvar.textContent = campoId.value
                ? "Salvar alterações"
                : "Salvar veículo";
        }
    }

    // --------------------------------------------------
    // EXCLUIR VEÍCULO
    // --------------------------------------------------

    async function excluirVeiculo(veiculo) {
        if (!ehAdministrador) {
            mostrarMensagemLista(
                "Seu perfil permite apenas consultar veículos.",
                "erro"
            );
            return;
        }

        const id = veiculo.id_veiculo ?? veiculo.id;

        if (!id) {
            mostrarMensagemLista(
                "Não foi possível identificar o veículo.",
                "erro"
            );
            return;
        }

        const confirmado = confirm(
            `Deseja realmente excluir o veículo ${veiculo.placa ?? ""}?`
        );

        if (!confirmado) {
            return;
        }

        try {
            await requisicaoAPI(
                `${API_VEICULOS}/${encodeURIComponent(id)}`,
                { method: "DELETE" }
            );

            await carregarTudo();

            mostrarMensagemLista(
                "Veículo desativado com sucesso.",
                "sucesso"
            );
        } catch (erro) {
            console.error(
                "Erro ao excluir veículo:",
                erro
            );

            mostrarMensagemLista(
                erro.message ||
                    "Não foi possível excluir o veículo.",
                "erro"
            );
        }
    }

    // --------------------------------------------------
    // EVENTOS DA PÁGINA
    // --------------------------------------------------

    botaoNovoVeiculo?.addEventListener(
        "click",
        abrirNovoVeiculo
    );

    botaoCancelar?.addEventListener(
        "click",
        fecharFormulario
    );

    formulario?.addEventListener(
        "submit",
        salvarVeiculo
    );

    pesquisa?.addEventListener(
        "input",
        renderizarVeiculos
    );

    campoMarca?.addEventListener(
        "change",
        async () => {
            if (!ehAdministrador) {
                return;
            }

            try {
                await carregarModelos(campoMarca.value);
            } catch (erro) {
                mostrarMensagem(
                    `Erro ao carregar modelos: ${erro.message}`,
                    "erro"
                );
            }
        }
    );

    // A consulta é permitida para os dois perfis.
    carregarTudo();
}
