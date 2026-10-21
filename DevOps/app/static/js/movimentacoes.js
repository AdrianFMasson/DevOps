document.addEventListener("DOMContentLoaded", () => {
    const API = "/api/movimentacoes";

    const tabela = document.querySelector("#tabelaMovimentacoes tbody");
    const campoBusca = document.querySelector("#buscaMovimentacao");
    const filtroStatus = document.querySelector("#filtroStatus");

    let movimentacoes = [];

    async function requisicao(url, opcoes = {}) {
        const resposta = await fetch(url, {
            headers: { "Content-Type": "application/json" },
            ...opcoes
        });

        if (!resposta.ok) {
            const erro = await resposta.json().catch(() => ({}));
            throw new Error(erro.detail || `Erro HTTP ${resposta.status}`);
        }

        if (resposta.status === 204) return null;
        return resposta.json();
    }

    function formatarData(data) {
        if (!data) return "—";

        return new Date(data).toLocaleString("pt-BR", {
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

    function escapar(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[caractere]);
    }

    function renderizarTabela() {
        if (!tabela) {
            console.error("Tabela não encontrada: confira o ID #tabelaMovimentacoes.");
            return;
        }

        const busca = (campoBusca?.value || "").toLowerCase();
        const status = filtroStatus?.value || "";

        const filtradas = movimentacoes.filter(item => {
            const texto = [
                item.id_movimentacao,
                item.id_veiculo,
                item.id_vaga,
                item.modalidade
            ].join(" ").toLowerCase();

            const situacao = item.data_hora_saida ? "fechada" : "aberta";

            return texto.includes(busca) && (!status || status === situacao);
        });

        if (!filtradas.length) {
            tabela.innerHTML = `
                <tr>
                    <td colspan="8">Nenhuma movimentação encontrada.</td>
                </tr>`;
            return;
        }

        tabela.innerHTML = filtradas.map(item => `
            <tr>
                <td>${escapar(item.id_movimentacao)}</td>
                <td>${escapar(item.id_veiculo)}</td>
                <td>${escapar(item.id_vaga)}</td>
                <td>${escapar(item.modalidade)}</td>
                <td>${formatarData(item.data_hora_entrada)}</td>
                <td>${formatarData(item.data_hora_saida)}</td>
                <td>${formatarValor(item.valor_total)}</td>
                <td>
                    ${item.data_hora_saida
                        ? '<span class="status-fechado">Fechada</span>'
                        : `<button type="button" class="btn-saida"
                            data-saida="${escapar(item.id_movimentacao)}">
                            Registrar saída
                           </button>`
                    }
                </td>
            </tr>
        `).join("");
    }

    async function carregarMovimentacoes() {
        try {
            tabela && (tabela.innerHTML = `
                <tr><td colspan="8">Carregando movimentações...</td></tr>
            `);

            movimentacoes = await requisicao(API);
            renderizarTabela();
            atualizarMetricas();
        } catch (erro) {
            console.error("Erro ao carregar movimentações:", erro);

            if (tabela) {
                tabela.innerHTML = `
                    <tr>
                        <td colspan="8">
                            Não foi possível carregar as movimentações.
                            Verifique a API e tente novamente.
                        </td>
                    </tr>`;
            }
        }
    }

    function atualizarMetricas() {
        const abertas = movimentacoes.filter(item => !item.data_hora_saida);
        const fechadas = movimentacoes.filter(item => item.data_hora_saida);

        const total = document.querySelector("#totalMovimentacoes");
        const totalAbertas = document.querySelector("#movimentacoesAbertas");
        const totalFechadas = document.querySelector("#movimentacoesFechadas");

        if (total) total.textContent = movimentacoes.length;
        if (totalAbertas) totalAbertas.textContent = abertas.length;
        if (totalFechadas) totalFechadas.textContent = fechadas.length;
    }

    async function registrarEntrada(dados) {
        try {
            await requisicao(API, {
                method: "POST",
                body: JSON.stringify(dados)
            });

            alert("Entrada registrada com sucesso.");
            await carregarMovimentacoes();
        } catch (erro) {
            alert(`Erro ao registrar entrada: ${erro.message}`);
        }
    }

    async function registrarSaida(id, dados) {
        try {
            await requisicao(`${API}/${id}/saida`, {
                method: "PATCH",
                body: JSON.stringify(dados)
            });

            alert("Saída registrada com sucesso.");
            await carregarMovimentacoes();
        } catch (erro) {
            alert(`Erro ao registrar saída: ${erro.message}`);
        }
    }

    campoBusca?.addEventListener("input", renderizarTabela);
    filtroStatus?.addEventListener("change", renderizarTabela);

    tabela?.addEventListener("click", async evento => {
        const botao = evento.target.closest("[data-saida]");
        if (!botao) return;

        const idUsuario = prompt("Informe o ID do usuário que registra a saída:");
        if (!idUsuario || !Number.isInteger(Number(idUsuario)) || Number(idUsuario) <= 0) {
            return;
        }

        await registrarSaida(Number(botao.dataset.saida), {
            id_usuario_saida: Number(idUsuario)
        });
    });

    // Disponibiliza funções para os formulários da página.
    window.carregarMovimentacoes = carregarMovimentacoes;
    window.registrarEntrada = registrarEntrada;
    window.registrarSaida = registrarSaida;

    carregarMovimentacoes();
});