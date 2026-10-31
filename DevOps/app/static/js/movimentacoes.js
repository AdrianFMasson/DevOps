
"use strict";

document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // CONFIGURAÇÃO DAS APIs
    // =========================================================

    const API = {
        movimentacoes: "/api/movimentacoes",
        clientes: "/api/movimentacoes/clientes",

        veiculos: (idCliente) =>
            `/api/movimentacoes/clientes/${encodeURIComponent(idCliente)}/veiculos`,

        vagas: (idVeiculo, modalidade) =>
            `/api/movimentacoes/veiculos/${encodeURIComponent(idVeiculo)}/vagas?modalidade=${encodeURIComponent(modalidade)}`,

        tarifas: "/api/movimentacoes/tarifas/vigentes"
    };

    // =========================================================
    // ELEMENTOS HTML
    // =========================================================

    const elemento = (id) => document.getElementById(id);

    const tabela = elemento("tabelaMovimentacoes");
    const campoBusca = elemento("buscaMovimentacao");
    const filtroStatus = elemento("filtroStatus");

    const modalEntrada = elemento("modalEntrada");
    const modalSaida = elemento("modalSaida");

    const formEntrada = elemento("formEntrada");
    const formSaida = elemento("formSaida");

    const entradaCliente = elemento("entradaCliente");
    const entradaVeiculo = elemento("entradaVeiculo");
    const entradaModalidade = elemento("entradaModalidade");
    const entradaVaga = elemento("entradaVaga");
    const entradaTarifa = elemento("entradaTarifa");

    const grupoTarifa = elemento("grupoTarifa");
    const botaoConfirmarEntrada = elemento("confirmarEntrada");

    const saidaMovimentacao = elemento("saidaMovimentacao");
    const resumoSaida = elemento("resumoSaida");

    const notificacao = elemento("notificacao");

    // =========================================================
    // ESTADO
    // =========================================================

    let movimentacoes = [];
    let clientes = [];
    let veiculos = [];
    let vagas = [];
    let tarifas = [];

    let carregando = false;

    // =========================================================
    // REQUISIÇÕES HTTP
    // =========================================================

    async function requisicao(url, opcoes = {}) {

        const resposta = await fetch(url, {
            credentials: "same-origin",
            ...opcoes,

            headers: {
                Accept: "application/json",

                ...(opcoes.body
                    ? { "Content-Type": "application/json" }
                    : {}),

                ...opcoes.headers
            }
        });

        if (resposta.status === 204) {
            return null;
        }

        const texto = await resposta.text();

        let dados = null;

        if (texto) {
            try {
                dados = JSON.parse(texto);
            } catch {
                dados = texto;
            }
        }

        if (!resposta.ok) {

            let mensagem = `Erro HTTP ${resposta.status}`;

            if (typeof dados === "string") {
                mensagem = dados;

            } else if (dados?.detail) {

                mensagem = Array.isArray(dados.detail)
                    ? dados.detail.map(item => item.msg).join(", ")
                    : dados.detail;

            } else if (dados?.message) {
                mensagem = dados.message;
            }

            throw new Error(mensagem);
        }

        return dados;
    }

    function obterLista(dados, propriedades = []) {

        if (Array.isArray(dados)) {
            return dados;
        }

        for (const propriedade of propriedades) {

            if (Array.isArray(dados?.[propriedade])) {
                return dados[propriedade];
            }
        }

        return [];
    }

    // =========================================================
    // FUNÇÕES AUXILIARES
    // =========================================================

    function escapar(valor) {

        return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[caractere]);
    }

    function formatarData(data) {

        if (!data) return "—";

        const dataFormatada = new Date(data);

        if (Number.isNaN(dataFormatada.getTime())) {
            return "—";
        }

        return dataFormatada.toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    function formatarValor(valor) {

        if (valor == null) return "—";

        return Number(valor).toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL"
        });
    }

    function normalizarTexto(valor) {

        return String(valor ?? "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toUpperCase()
            .trim();
    }

    function mostrarNotificacao(mensagem, tipo = "") {

        if (typeof window.mostrarNotificacao === "function") {
            window.mostrarNotificacao(mensagem, tipo);
            return;
        }

        if (!notificacao) {
            alert(mensagem);
            return;
        }

        notificacao.textContent = mensagem;
        notificacao.className = "notificacao";

        if (tipo) {
            notificacao.classList.add(tipo);
        }

        notificacao.classList.add("visivel");

        setTimeout(() => {
            notificacao.classList.remove("visivel");
        }, 4000);
    }

    function preencherSelect(select, lista, configuracao = {}) {

        if (!select) return;

        const {
            placeholder = "Selecione uma opção",
            valor = "id",
            texto = "nome"
        } = configuracao;

        select.innerHTML = "";

        const opcaoInicial = document.createElement("option");

        opcaoInicial.value = "";
        opcaoInicial.textContent = placeholder;

        select.appendChild(opcaoInicial);

        lista.forEach(item => {

            const opcao = document.createElement("option");

            opcao.value = item[valor];
            opcao.textContent = item[texto];

            select.appendChild(opcao);
        });
    }

    // =========================================================
    // DADOS DOS REGISTROS
    // =========================================================

    function obterNomeDoClienteMovimentacao(item) {
        return item.cliente ?? "—";
    }

    function obterVeiculoMovimentacao(item) {

        return [
            item.placa,
            item.veiculo
        ].filter(Boolean).join(" - ") || "—";
    }

    function obterVagaMovimentacao(item) {
        return item.vaga ?? "—";
    }

    // =========================================================
    // CARREGAR CLIENTES
    // =========================================================

    async function carregarClientes() {

        const dados = await requisicao(API.clientes);

        clientes = obterLista(dados);

        preencherSelect(
            entradaCliente,
            clientes.map(cliente => ({
                id: cliente.id,
                nome: cliente.nome
            })),
            {
                placeholder: "Selecione o cliente",
                valor: "id",
                texto: "nome"
            }
        );

        return clientes;
    }

    // =========================================================
    // CARREGAR VEÍCULOS DO CLIENTE
    // =========================================================

    async function carregarVeiculos(idCliente) {

        if (!entradaVeiculo) return;

        entradaVeiculo.disabled = true;

        preencherSelect(entradaVeiculo, [], {
            placeholder: "Carregando veículos..."
        });

        veiculos = [];

        if (!idCliente) {

            preencherSelect(entradaVeiculo, [], {
                placeholder: "Selecione primeiro um cliente"
            });

            return;
        }

        try {

            const dados = await requisicao(
                API.veiculos(idCliente)
            );

            veiculos = obterLista(dados);

            preencherSelect(
                entradaVeiculo,
                veiculos.map(veiculo => ({
                    id: veiculo.id,
                    nome: veiculo.descricao
                })),
                {
                    placeholder: veiculos.length
                        ? "Selecione o veículo"
                        : "Nenhum veículo encontrado",

                    valor: "id",
                    texto: "nome"
                }
            );

            entradaVeiculo.disabled = veiculos.length === 0;

        } catch (erro) {

            console.error("Erro ao carregar veículos:", erro);

            preencherSelect(entradaVeiculo, [], {
                placeholder: "Erro ao carregar veículos"
            });

            mostrarNotificacao(
                `Não foi possível carregar os veículos: ${erro.message}`,
                "erro"
            );
        }
    }

    // =========================================================
    // CARREGAR VAGAS DISPONÍVEIS
    // =========================================================

    async function carregarVagas(idVeiculo, modalidade) {

        if (!entradaVaga) return;

        entradaVaga.disabled = true;

        preencherSelect(entradaVaga, [], {
            placeholder: "Carregando vagas..."
        });

        vagas = [];

        if (!idVeiculo || !modalidade) {

            preencherSelect(entradaVaga, [], {
                placeholder: "Selecione o veículo e a modalidade"
            });

            return;
        }

        try {

            const dados = await requisicao(
                API.vagas(idVeiculo, modalidade)
            );

            vagas = obterLista(dados);

            preencherSelect(
                entradaVaga,
                vagas.map(vaga => ({
                    id: vaga.id,
                    nome: vaga.descricao
                })),
                {
                    placeholder: vagas.length
                        ? "Selecione a vaga"
                        : "Nenhuma vaga disponível",

                    valor: "id",
                    texto: "nome"
                }
            );

            entradaVaga.disabled = vagas.length === 0;

        } catch (erro) {

            console.error("Erro ao carregar vagas:", erro);

            preencherSelect(entradaVaga, [], {
                placeholder: "Erro ao carregar vagas"
            });

            mostrarNotificacao(
                `Não foi possível carregar as vagas: ${erro.message}`,
                "erro"
            );
        }
    }

    // =========================================================
    // CARREGAR TARIFAS VIGENTES
    // =========================================================

    async function carregarTarifas() {

        if (!entradaTarifa) return;

        entradaTarifa.disabled = true;

        preencherSelect(entradaTarifa, [], {
            placeholder: "Carregando tarifas..."
        });

        tarifas = [];

        try {

            const dados = await requisicao(API.tarifas);

            tarifas = obterLista(dados);

            preencherSelect(
                entradaTarifa,
                tarifas.map(tarifa => ({
                    id: tarifa.id,
                    nome: `${tarifa.nome} - ${formatarValor(tarifa.valor_hora)}`
                })),
                {
                    placeholder: tarifas.length
                        ? "Selecione a tarifa"
                        : "Nenhuma tarifa vigente",

                    valor: "id",
                    texto: "nome"
                }
            );

            entradaTarifa.disabled = tarifas.length === 0;

        } catch (erro) {

            console.error("Erro ao carregar tarifas:", erro);

            preencherSelect(entradaTarifa, [], {
                placeholder: "Erro ao carregar tarifas"
            });

            mostrarNotificacao(
                `Não foi possível carregar as tarifas: ${erro.message}`,
                "erro"
            );
        }
    }

    // =========================================================
    // RENDERIZAR TABELA
    // =========================================================

    function renderizarTabela() {

        if (!tabela) {
            console.error(
                "Elemento #tabelaMovimentacoes não encontrado."
            );
            return;
        }

        const busca = normalizarTexto(campoBusca?.value);

        const status = filtroStatus?.value ?? "TODAS";

        const filtradas = movimentacoes.filter(item => {

            const texto = normalizarTexto([
                item.id,
                obterNomeDoClienteMovimentacao(item),
                obterVeiculoMovimentacao(item),
                obterVagaMovimentacao(item),
                item.modalidade
            ].join(" "));

            const fechada = Boolean(item.data_hora_saida);

            const correspondeStatus =
                status === "TODAS" ||
                (status === "ABERTAS" && !fechada) ||
                (status === "FECHADAS" && fechada);

            return texto.includes(busca) && correspondeStatus;
        });

        if (!filtradas.length) {

            tabela.innerHTML = `
                <tr>
                    <td colspan="9">
                        Nenhuma movimentação encontrada.
                    </td>
                </tr>
            `;

            atualizarQuantidadeTabela(0);

            return;
        }

        tabela.innerHTML = filtradas.map(item => {

            const fechada = Boolean(item.data_hora_saida);

            const statusHtml = fechada
                ? `<span class="status-fechado">Fechada</span>`
                : `<span class="status-aberto">Aberta</span>`;

            const acoesHtml = fechada
                ? "—"
                : `
                    <button
                        type="button"
                        class="btn-saida"
                        data-saida="${escapar(item.id)}"
                    >
                        Registrar saída
                    </button>
                `;

            return `
                <tr>
                    <td>${escapar(obterNomeDoClienteMovimentacao(item))}</td>

                    <td>${escapar(obterVeiculoMovimentacao(item))}</td>

                    <td>${escapar(obterVagaMovimentacao(item))}</td>

                    <td>${escapar(item.modalidade ?? "—")}</td>

                    <td>${formatarData(item.data_hora_entrada)}</td>

                    <td>${formatarData(item.data_hora_saida)}</td>

                    <td>${formatarValor(item.valor_total)}</td>

                    <td>${statusHtml}</td>

                    <td>${acoesHtml}</td>
                </tr>
            `;

        }).join("");

        atualizarQuantidadeTabela(filtradas.length);
    }

    // =========================================================
    // ATUALIZAR QUANTIDADE
    // =========================================================

    function atualizarQuantidadeTabela(quantidade) {

        const elementoQuantidade = elemento(
            "quantidadeMovimentacoes"
        );

        if (elementoQuantidade) {
            elementoQuantidade.textContent = quantidade;
        }
    }

    // =========================================================
    // ATUALIZAR INDICADORES
    // =========================================================

    function atualizarMetricas() {

        const abertas = movimentacoes.filter(
            item => !item.data_hora_saida
        );

        const fechadas = movimentacoes.filter(
            item => Boolean(item.data_hora_saida)
        );

        const total = elemento("totalMovimentacoes");

        const totalAbertas = elemento("movimentacoesAbertas");

        const totalFechadas = elemento("movimentacoesFechadas");

        if (total) {
            total.textContent = movimentacoes.length;
        }

        if (totalAbertas) {
            totalAbertas.textContent = abertas.length;
        }

        if (totalFechadas) {
            totalFechadas.textContent = fechadas.length;
        }

        const receita = elemento("receitaMovimentacoes");

        if (receita) {

            const valorTotal = movimentacoes.reduce(
                (soma, item) => soma + Number(item.valor_total ?? 0),
                0
            );

            receita.textContent = formatarValor(valorTotal);
        }
    }

    // =========================================================
    // CARREGAR MOVIMENTAÇÕES
    // =========================================================

    async function carregarMovimentacoes() {

        if (carregando) return;

        carregando = true;

        if (tabela) {

            tabela.innerHTML = `
                <tr>
                    <td colspan="9">
                        Carregando movimentações...
                    </td>
                </tr>
            `;
        }

        try {

            const dados = await requisicao(
                API.movimentacoes
            );

            movimentacoes = obterLista(dados);

            renderizarTabela();

            atualizarMetricas();

        } catch (erro) {

            console.error(
                "Erro ao carregar movimentações:",
                erro
            );

            if (tabela) {

                tabela.innerHTML = `
                    <tr>
                        <td colspan="9">
                            Não foi possível carregar as movimentações.
                            ${escapar(erro.message)}
                        </td>
                    </tr>
                `;
            }

            mostrarNotificacao(
                `Erro ao carregar movimentações: ${erro.message}`,
                "erro"
            );

        } finally {

            carregando = false;
        }
    }

    // =========================================================
    // ATUALIZAR CAMPOS DA MODALIDADE
    // =========================================================

    function atualizarCamposModalidade() {

        const modalidade = entradaModalidade?.value;

        const horista = modalidade === "HORISTA";

        if (grupoTarifa) {
            grupoTarifa.hidden = !horista;
        }

        if (entradaTarifa) {
            entradaTarifa.required = horista;

            if (!horista) {
                entradaTarifa.value = "";
            }
        }

        if (entradaVaga) {

            entradaVaga.disabled = true;

            preencherSelect(entradaVaga, [], {
                placeholder: "Selecione o veículo e a modalidade"
            });
        }
    }

    // =========================================================
    // ABRIR MODAL DE ENTRADA
    // =========================================================

    async function abrirFormularioEntrada() {

        if (!formEntrada) return;

        formEntrada.reset();

        atualizarCamposModalidade();

        if (entradaCliente) {

            entradaCliente.disabled = true;

            preencherSelect(entradaCliente, [], {
                placeholder: "Carregando clientes..."
            });
        }

        if (entradaVeiculo) {

            entradaVeiculo.disabled = true;

            preencherSelect(entradaVeiculo, [], {
                placeholder: "Selecione primeiro um cliente"
            });
        }

        if (entradaModalidade) {
            entradaModalidade.disabled = true;
        }

        if (entradaVaga) {
            entradaVaga.disabled = true;
        }

        if (grupoTarifa) {
            grupoTarifa.hidden = true;
        }

        if (typeof window.abrirModal === "function") {

            window.abrirModal("modalEntrada");

        } else {

            modalEntrada?.classList.add("aberto");

            modalEntrada?.setAttribute("aria-hidden", "false");
        }

        try {

            await carregarClientes();

            if (entradaCliente) {
                entradaCliente.disabled = false;
            }

            if (!clientes.length) {

                mostrarNotificacao(
                    "Não existem clientes cadastrados.",
                    "erro"
                );
            }

        } catch (erro) {

            console.error(
                "Erro ao abrir formulário:",
                erro
            );

            mostrarNotificacao(
                `Não foi possível carregar os clientes: ${erro.message}`,
                "erro"
            );
        }
    }

    // =========================================================
    // SELECIONAR CLIENTE
    // =========================================================

    async function selecionarCliente() {

        const idCliente = entradaCliente?.value;

        veiculos = [];
        vagas = [];

        if (entradaVeiculo) {
            entradaVeiculo.disabled = true;
        }

        if (entradaModalidade) {

            entradaModalidade.disabled = true;

            entradaModalidade.value = "";
        }

        if (entradaVaga) {

            entradaVaga.disabled = true;

            preencherSelect(entradaVaga, [], {
                placeholder: "Selecione a modalidade"
            });
        }

        if (grupoTarifa) {
            grupoTarifa.hidden = true;
        }

        if (entradaTarifa) {
            entradaTarifa.value = "";
        }

        if (!idCliente) {

            preencherSelect(entradaVeiculo, [], {
                placeholder: "Selecione primeiro um cliente"
            });

            return;
        }

        await carregarVeiculos(idCliente);

        if (veiculos.length && entradaModalidade) {
            entradaModalidade.disabled = false;
        }
    }

    // =========================================================
    // SELECIONAR VEÍCULO
    // =========================================================

    async function selecionarVeiculo() {

        const idVeiculo = entradaVeiculo?.value;

        vagas = [];

        if (entradaVaga) {

            entradaVaga.disabled = true;

            preencherSelect(entradaVaga, [], {
                placeholder: "Selecione a modalidade"
            });
        }

        if (entradaModalidade) {

            entradaModalidade.value = "";

            entradaModalidade.disabled = !idVeiculo;
        }

        if (entradaTarifa) {
            entradaTarifa.value = "";
        }

        if (grupoTarifa) {
            grupoTarifa.hidden = true;
        }
    }

    // =========================================================
    // SELECIONAR MODALIDADE
    // =========================================================

    async function selecionarModalidade() {

        const idVeiculo = entradaVeiculo?.value;

        const modalidade = entradaModalidade?.value;

        atualizarCamposModalidade();

        if (!idVeiculo || !modalidade) return;

        if (modalidade === "HORISTA") {
            await carregarTarifas();
        }

        await carregarVagas(idVeiculo, modalidade);
    }

    // =========================================================
    // REGISTRAR ENTRADA
    // =========================================================

    async function registrarEntrada(evento) {

        evento.preventDefault();

        if (!formEntrada) return;

        const idCliente = entradaCliente?.value;

        const idVeiculo = entradaVeiculo?.value;

        const modalidade = entradaModalidade?.value;

        const idVaga = entradaVaga?.value;

        const idTarifa = entradaTarifa?.value;

        if (
            !idCliente ||
            !idVeiculo ||
            !modalidade ||
            !idVaga
        ) {

            mostrarNotificacao(
                "Preencha todos os campos obrigatórios.",
                "erro"
            );

            return;
        }

        if (
            modalidade === "HORISTA" &&
            !idTarifa
        ) {

            mostrarNotificacao(
                "Selecione uma tarifa para a modalidade horista.",
                "erro"
            );

            return;
        }

        const dados = {
            id_veiculo: Number(idVeiculo),
            id_vaga: Number(idVaga),
            modalidade: modalidade
        };

        if (modalidade === "HORISTA") {
            dados.id_tarifa = Number(idTarifa);
        }

        try {

            if (botaoConfirmarEntrada) {

                botaoConfirmarEntrada.disabled = true;

                botaoConfirmarEntrada.textContent = "Registrando...";
            }

            await requisicao(API.movimentacoes, {
                method: "POST",
                body: JSON.stringify(dados)
            });

            mostrarNotificacao(
                "Entrada registrada com sucesso!",
                "sucesso"
            );

            if (typeof window.fecharModal === "function") {

                window.fecharModal("modalEntrada");

            } else {

                modalEntrada?.classList.remove("aberto");

                modalEntrada?.setAttribute("aria-hidden", "true");
            }

            formEntrada.reset();

            atualizarCamposModalidade();

            await carregarMovimentacoes();

        } catch (erro) {

            console.error(
                "Erro ao registrar entrada:",
                erro
            );

            mostrarNotificacao(
                `Não foi possível registrar a entrada: ${erro.message}`,
                "erro"
            );

        } finally {

            if (botaoConfirmarEntrada) {

                botaoConfirmarEntrada.disabled = false;

                botaoConfirmarEntrada.textContent = "Confirmar entrada";
            }
        }
    }

    // =========================================================
    // ABRIR MODAL DE SAÍDA
    // =========================================================

    function abrirFormularioSaida(id, resumo = "") {

        if (saidaMovimentacao) {
            saidaMovimentacao.value = id;
        }

        if (resumoSaida) {
            resumoSaida.textContent = resumo;
        }

        if (typeof window.abrirModalSaida === "function") {

            window.abrirModalSaida(id, resumo);

            return;
        }

        if (typeof window.abrirModal === "function") {

            window.abrirModal("modalSaida");

        } else {

            modalSaida?.classList.add("aberto");

            modalSaida?.setAttribute("aria-hidden", "false");
        }
    }

    // =========================================================
    // REGISTRAR SAÍDA
    // =========================================================

    async function registrarSaida(evento) {

        evento.preventDefault();

        const id = saidaMovimentacao?.value;

        if (!id) {

            mostrarNotificacao(
                "Não foi possível identificar a movimentação.",
                "erro"
            );

            return;
        }

        const botao = formSaida?.querySelector(
            'button[type="submit"]'
        );

        try {

            if (botao) {

                botao.disabled = true;

                botao.textContent = "Registrando...";
            }

            // O backend define:
            // - usuário responsável pela saída;
            // - data e hora da saída;
            // - valor total da cobrança.

            const resposta = await requisicao(
                `${API.movimentacoes}/${encodeURIComponent(id)}/saida`,
                {
                    method: "PATCH",
                    body: JSON.stringify({})
                }
            );

            mostrarNotificacao(
                resposta?.mensagem || "Saída registrada com sucesso!",
                "sucesso"
            );

            if (typeof window.fecharModal === "function") {

                window.fecharModal("modalSaida");

            } else {

                modalSaida?.classList.remove("aberto");

                modalSaida?.setAttribute("aria-hidden", "true");
            }

            formSaida?.reset();

            await carregarMovimentacoes();

        } catch (erro) {

            console.error(
                "Erro ao registrar saída:",
                erro
            );

            mostrarNotificacao(
                `Não foi possível registrar a saída: ${erro.message}`,
                "erro"
            );

        } finally {

            if (botao) {

                botao.disabled = false;

                botao.textContent = "Confirmar saída";
            }
        }
    }

    // =========================================================
    // EVENTOS DOS FORMULÁRIOS
    // =========================================================

    campoBusca?.addEventListener(
        "input",
        renderizarTabela
    );

    filtroStatus?.addEventListener(
        "change",
        renderizarTabela
    );

    entradaCliente?.addEventListener(
        "change",
        selecionarCliente
    );

    entradaVeiculo?.addEventListener(
        "change",
        selecionarVeiculo
    );

    entradaModalidade?.addEventListener(
        "change",
        selecionarModalidade
    );

    formEntrada?.addEventListener(
        "submit",
        registrarEntrada
    );

    formSaida?.addEventListener(
        "submit",
        registrarSaida
    );

    // =========================================================
    // EVENTO DO BOTÃO REGISTRAR SAÍDA
    // =========================================================

    tabela?.addEventListener("click", evento => {

        const botao = evento.target.closest("[data-saida]");

        if (!botao) return;

        const id = botao.dataset.saida;

        const movimentacao = movimentacoes.find(
            item => String(item.id) === String(id)
        );

        if (!movimentacao) {

            mostrarNotificacao(
                "Movimentação não encontrada.",
                "erro"
            );

            return;
        }

        if (movimentacao.data_hora_saida) {

            mostrarNotificacao(
                "Esta movimentação já foi encerrada.",
                "erro"
            );

            return;
        }

        const resumo = [
            `Cliente: ${obterNomeDoClienteMovimentacao(movimentacao)}`,
            `Veículo: ${obterVeiculoMovimentacao(movimentacao)}`,
            `Vaga: ${obterVagaMovimentacao(movimentacao)}`,
            `Entrada: ${formatarData(movimentacao.data_hora_entrada)}`
        ].join(" | ");

        abrirFormularioSaida(id, resumo);
    });

    // =========================================================
    // BOTÃO ABRIR MODAL DE ENTRADA
    // =========================================================

    elemento("abrirModalEntrada")?.addEventListener(
        "click",
        abrirFormularioEntrada
    );

    // =========================================================
    // BOTÃO ATUALIZAR MOVIMENTAÇÕES
    // =========================================================

    elemento("atualizarMovimentacoes")?.addEventListener(
        "click",
        carregarMovimentacoes
    );

    // =========================================================
    // FUNÇÕES DISPONÍVEIS NA PÁGINA
    // =========================================================

    window.carregarMovimentacoes = carregarMovimentacoes;

    window.registrarEntrada = registrarEntrada;

    window.registrarSaida = registrarSaida;

    window.abrirFormularioEntrada = abrirFormularioEntrada;

    window.abrirFormularioSaida = abrirFormularioSaida;

    // =========================================================
    // INICIALIZAÇÃO
    // =========================================================

    carregarMovimentacoes();

});
