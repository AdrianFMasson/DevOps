
"use strict";

document.addEventListener("DOMContentLoaded", iniciarDashboard);

function iniciarDashboard() {
    const API_VEICULOS = "/api/veiculos";
    const API_VAGAS = "/api/vagas";
    const API_LOGOUT = "/api/logout";

    const elemento = (id) => document.getElementById(id);

    const totalVeiculos = elemento("total-veiculos");
    const totalVagas = elemento("total-vagas");
    const vagasDisponiveis = elemento("vagas-disponiveis");
    const vagasOcupadas = elemento("vagas-ocupadas");

    const mensagem = elemento("mensagem-dashboard");
    const ultimaAtualizacao = elemento("ultima-atualizacao");
    const botaoAtualizar = elemento("botao-atualizar");
    const botaoSair = elemento("botao-sair");

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

        if (Array.isArray(dados?.data)) {
            return dados.data;
        }

        return [];
    }

    async function requisicaoAPI(url) {
        const resposta = await window.apiFetch(url, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        const texto = await resposta.text();

        let dados = null;

        if (texto) {
            try {
                dados = JSON.parse(texto);
            } catch {
                dados = {
                    detail: texto
                };
            }
        }

        if (!resposta.ok) {
            const detalhe =
                dados?.detail ||
                dados?.mensagem ||
                dados?.message ||
                `Erro HTTP ${resposta.status}`;

            throw new Error(String(detalhe));
        }

        return dados;
    }

    function mostrarMensagem(texto, tipo = "") {
        if (!mensagem) return;

        mensagem.textContent = texto;
        mensagem.className = "mensagem-dashboard";

        if (tipo) {
            mensagem.classList.add(tipo);
        }
    }

    function atualizarIndicador(elementoIndicador, valor) {
        if (!elementoIndicador) return;

        elementoIndicador.textContent =
            valor == null ? "—" : String(valor);
    }

    function normalizarStatus(valor) {
        return String(valor ?? "")
            .trim()
            .toLocaleLowerCase("pt-BR")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .replace(/[_-]+/g, " ");
    }

    function obterStatusVaga(vaga) {
        return normalizarStatus(
            vaga.status ??
            vaga.situacao ??
            vaga.estado ??
            vaga.status_vaga ??
            ""
        );
    }

    function vagaEstaDisponivel(vaga) {
        const status = obterStatusVaga(vaga);

        return [
            "disponivel",
            "livre",
            "desocupada",
            "vaga livre"
        ].includes(status);
    }

    function vagaEstaOcupada(vaga) {
        const status = obterStatusVaga(vaga);

        return [
            "ocupada",
            "em uso",
            "reservada ocupada"
        ].includes(status);
    }

    function atualizarResumoVeiculos(veiculos) {
        atualizarIndicador(
            totalVeiculos,
            veiculos.length
        );
    }

    function atualizarResumoVagas(vagas) {
        const disponiveis = vagas.filter(
            vagaEstaDisponivel
        ).length;

        const ocupadas = vagas.filter(
            vagaEstaOcupada
        ).length;

        atualizarIndicador(
            totalVagas,
            vagas.length
        );

        atualizarIndicador(
            vagasDisponiveis,
            disponiveis
        );

        atualizarIndicador(
            vagasOcupadas,
            ocupadas
        );

        const desconhecidas =
            vagas.length - disponiveis - ocupadas;

        return {
            total: vagas.length,
            disponiveis,
            ocupadas,
            desconhecidas
        };
    }

    function formatarDataHora(data = new Date()) {
        return new Intl.DateTimeFormat("pt-BR", {
            dateStyle: "short",
            timeStyle: "short"
        }).format(data);
    }

    function atualizarHorario() {
        if (!ultimaAtualizacao) return;

        ultimaAtualizacao.textContent =
            `Última atualização: ${formatarDataHora()}`;
    }

    async function carregarVeiculos() {
        const dados = await requisicaoAPI(API_VEICULOS);
        const veiculos = obterLista(dados, "veiculos");

        atualizarResumoVeiculos(veiculos);

        return veiculos;
    }

    async function carregarVagas() {
        const dados = await requisicaoAPI(API_VAGAS);
        const vagas = obterLista(dados, "vagas");

        return atualizarResumoVagas(vagas);
    }

    async function carregarDashboard() {
        if (botaoAtualizar) {
            botaoAtualizar.disabled = true;
            botaoAtualizar.textContent = "Atualizando...";
        }

        mostrarMensagem("Consultando dados do estacionamento...");

        try {
            const resultados = await Promise.allSettled([
                carregarVeiculos(),
                carregarVagas()
            ]);

            const erros = [];

            if (resultados[0].status === "rejected") {
                atualizarIndicador(totalVeiculos, null);

                console.error(
                    "Erro ao carregar veículos:",
                    resultados[0].reason
                );

                erros.push(
                    "Não foi possível carregar os veículos."
                );
            }

            if (resultados[1].status === "rejected") {
                atualizarIndicador(totalVagas, null);
                atualizarIndicador(vagasDisponiveis, null);
                atualizarIndicador(vagasOcupadas, null);

                console.error(
                    "Erro ao carregar vagas:",
                    resultados[1].reason
                );

                erros.push(
                    "Não foi possível carregar as vagas."
                );
            }

            if (erros.length > 0) {
                mostrarMensagem(
                    erros.join(" ") +
                    " Verifique a conexão com o servidor e as rotas da API.",
                    "erro"
                );
            } else {
                mostrarMensagem(
                    "Indicadores atualizados com sucesso.",
                    "sucesso"
                );

                atualizarHorario();
            }
        } catch (erro) {
            console.error("Erro ao carregar dashboard:", erro);

            mostrarMensagem(
                "Não foi possível atualizar o dashboard.",
                "erro"
            );
        } finally {
            if (botaoAtualizar) {
                botaoAtualizar.disabled = false;
                botaoAtualizar.textContent = "↻ Atualizar dados";
            }
        }
    }

    function configurarSaida() {
        if (!botaoSair) return;

        botaoSair.addEventListener("click", async () => {
            const confirmado = window.confirm(
                "Deseja sair do painel operacional?"
            );

            if (!confirmado) return;

            botaoSair.disabled = true;
            botaoSair.textContent = "Saindo...";

            try {
                // O logout não deve tentar renovar a sessão.
                const resposta = await fetch(API_LOGOUT, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json"
                    }
                });

                if (!resposta.ok) {
                    throw new Error(
                        `Não foi possível encerrar a sessão. HTTP ${resposta.status}`
                    );
                }

                window.location.replace("/");
            } catch (erro) {
                console.error("Erro ao sair:", erro);

                mostrarMensagem(
                    "Não foi possível encerrar a sessão. Tente novamente.",
                    "erro"
                );

                botaoSair.disabled = false;
                botaoSair.textContent = "Sair do sistema";
            }
        });
    }

    function configurarAtualizacao() {
        if (!botaoAtualizar) return;

        botaoAtualizar.addEventListener(
            "click",
            carregarDashboard
        );
    }

    configurarSaida();
    configurarAtualizacao();
    carregarDashboard();
}
