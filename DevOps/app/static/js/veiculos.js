"use strict";

const API_VEICULOS = "/api/veiculos";
const API_CLIENTES = "/api/clientes";
const API_MARCAS = "/api/marcas-veiculo";
const API_MODELOS = "/api/modelos-veiculo";

document.addEventListener("DOMContentLoaded", () => {
    const formulario = document.getElementById("formulario-veiculo");
    const painelFormulario = document.getElementById("painel-formulario-veiculo");
    const botaoNovo = document.getElementById("botao-novo-veiculo");
    const botaoCancelar = document.getElementById("botao-cancelar-veiculo");
    const botaoSalvar = document.getElementById("botao-salvar-veiculo");
    const tituloFormulario = document.getElementById("titulo-formulario-veiculo");
    const campoId = document.getElementById("id-veiculo");
    const campoPlaca = document.getElementById("placa-veiculo");
    const campoCor = document.getElementById("cor-veiculo");
    const campoMarca = document.getElementById("marca-veiculo");
    const campoModelo = document.getElementById("modelo-veiculo");
    const campoCliente = document.getElementById("cliente-veiculo");
    const campoMensalista = document.getElementById("mensalista-veiculo");
    const campoPesquisa = document.getElementById("pesquisa-veiculos");
    const listaVeiculos = document.getElementById("lista-veiculos");
    const mensagemFormulario = document.getElementById("mensagem-formulario-veiculo");
    const mensagemLista = document.getElementById("mensagem-lista-veiculos");

    let veiculos = [];
    let clientes = [];
    let marcas = [];
    let modelos = [];
    let carregando = false;

    if (!formulario || !painelFormulario || !listaVeiculos) {
        console.error("Os elementos HTML necessários para a página de veículos não foram encontrados.");
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
            throw new Error(
                Array.isArray(detalhe)
                    ? detalhe.map(item => {
                        const campo = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
                        return campo ? `${campo}: ${item.msg || "Dado inválido"}` : item.msg || String(item);
                    }).join("; ")
                    : String(detalhe)
            );
        }

        return dados;
    }

    function obterLista(dados, propriedade) {
        if (Array.isArray(dados)) return dados;
        const lista = dados?.[propriedade] ?? dados?.items ?? dados?.results ?? [];
        if (!Array.isArray(lista)) {
            throw new Error(`A API não retornou uma lista válida de ${propriedade}.`);
        }
        return lista;
    }

    function obterId(item) {
        return item.id_veiculo ?? item.id_marca ?? item.id_modelo ?? item.id_clients ?? item.id_cliente ?? item.id;
    }

    function obterPlaca(veiculo) {
        return veiculo.placa ?? veiculo.placa_veiculo ?? "";
    }

    function obterCor(veiculo) {
        return veiculo.cor ?? veiculo.cor_veiculo ?? "";
    }

    function obterMarcaId(veiculo) {
        return veiculo.id_marca ?? veiculo.id_marca_veiculo ?? veiculo.marca_id ?? veiculo.marca?.id_marca ?? veiculo.marca?.id;
    }

    function obterModeloId(veiculo) {
        return veiculo.id_modelo ?? veiculo.id_modelo_veiculo ?? veiculo.modelo_id ?? veiculo.modelo?.id_modelo ?? veiculo.modelo?.id;
    }

    function obterClienteId(veiculo) {
        return veiculo.id_clients ?? veiculo.id_cliente ?? veiculo.cliente_id ?? veiculo.cliente?.id_clients ?? veiculo.cliente?.id_cliente ?? veiculo.cliente?.id;
    }

    function obterNome(item) {
        return item.nome_completo ?? item.nome ?? item.nome_cliente ?? item.nome_marca ?? item.nome_modelo ?? item.descricao ?? "";
    }

    function obterNomeMarca(veiculo) {
        if (veiculo.marca && typeof veiculo.marca === "object") return obterNome(veiculo.marca);
        const marca = marcas.find(item => String(obterId(item)) === String(obterMarcaId(veiculo)));
        return marca ? obterNome(marca) : veiculo.nome_marca ?? veiculo.marca_nome ?? (typeof veiculo.marca === "string" ? veiculo.marca : "");
    }

    function obterNomeModelo(veiculo) {
        if (veiculo.modelo && typeof veiculo.modelo === "object") return obterNome(veiculo.modelo);
        const modelo = modelos.find(item => String(obterId(item)) === String(obterModeloId(veiculo)));
        return modelo ? obterNome(modelo) : veiculo.nome_modelo ?? veiculo.modelo_nome ?? (typeof veiculo.modelo === "string" ? veiculo.modelo : "");
    }

    function obterNomeCliente(veiculo) {
        if (veiculo.cliente && typeof veiculo.cliente === "object") return obterNome(veiculo.cliente);
        const cliente = clientes.find(item => String(obterId(item)) === String(obterClienteId(veiculo)));
        return cliente ? obterNome(cliente) : veiculo.nome_cliente ?? veiculo.cliente_nome ?? "";
    }

    function ehMensalista(veiculo) {
        const valor = veiculo.mensalista ?? veiculo.eh_mensalista ?? veiculo.is_mensalista ?? veiculo.tem_mensalidade;
        if (typeof valor === "boolean") return valor;
        if (typeof valor === "number") return valor === 1;
        if (typeof valor === "string") return ["sim", "true", "1", "ativo"].includes(valor.toLowerCase());
        return Boolean(veiculo.id_mensalista ?? veiculo.mensalista_id);
    }

    function veiculoAtivo(veiculo) {
        if (veiculo.ativo === undefined && veiculo.status === undefined) return true;
        return veiculo.ativo === true || veiculo.ativo === 1 || veiculo.status === "ATIVO" || veiculo.status === "ativo";
    }

    function criarCelula(texto) {
        const celula = document.createElement("td");
        celula.textContent = texto || "—";
        return celula;
    }

    function criarBotaoAcao(texto, classe, acao, id, rotulo) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = `botao-acao-veiculo ${classe}`.trim();
        botao.textContent = texto;
        botao.setAttribute("aria-label", rotulo);
        botao.addEventListener("click", () => acao(id));
        return botao;
    }

    function criarOpcao(valor, texto) {
        const opcao = document.createElement("option");
        opcao.value = valor ?? "";
        opcao.textContent = texto;
        return opcao;
    }

    function preencherSelect(campo, itens, textoInicial, selecionado = "") {
        campo.replaceChildren(criarOpcao("", textoInicial));

        itens.forEach(item => {
            campo.appendChild(criarOpcao(obterId(item), obterNome(item)));
        });

        campo.value = selecionado == null ? "" : String(selecionado);
    }

    async function carregarClientes() {
        try {
            clientes = obterLista(await requisicaoAPI(API_CLIENTES), "clientes");
            preencherSelect(campoCliente, clientes, "Selecione o cliente");
        } catch (erro) {
            console.error("Erro ao carregar clientes:", erro);
            clientes = [];
            preencherSelect(campoCliente, [], "Não foi possível carregar os clientes");
            mostrarMensagem(mensagemFormulario, "Não foi possível carregar os clientes. Verifique a API de clientes.", "erro");
        }
    }

    async function carregarMarcas() {
        try {
            marcas = obterLista(await requisicaoAPI(API_MARCAS), "marcas");
            preencherSelect(campoMarca, marcas, "Selecione a marca");
        } catch (erro) {
            console.error("Erro ao carregar marcas:", erro);
            marcas = [];
            preencherSelect(campoMarca, [], "Não foi possível carregar as marcas");
            mostrarMensagem(mensagemFormulario, "Não foi possível carregar as marcas. Confira a rota da API de marcas.", "erro");
        }
    }

    async function carregarModelos(idMarca, idSelecionado = "") {
        campoModelo.disabled = true;
        preencherSelect(campoModelo, [], idMarca ? "Carregando modelos..." : "Selecione primeiro a marca");

        if (!idMarca) return;

        try {
            const dados = await requisicaoAPI(API_MODELOS);
            const todosModelos = obterLista(dados, "modelos");

            modelos = todosModelos.filter(modelo =>
                String(modelo.id_marca) === String(idMarca) &&
                modelo.ativo !== false &&
                modelo.ativo !== 0
            );

            preencherSelect(campoModelo, modelos, "Selecione o modelo", idSelecionado);
            campoModelo.disabled = modelos.length === 0;

            if (modelos.length === 0) {
                preencherSelect(campoModelo, [], "Nenhum modelo disponível");
            }
        } catch (erro) {
            console.error("Erro ao carregar modelos:", erro);
            modelos = [];
            preencherSelect(campoModelo, [], "Erro ao carregar modelos");
            mostrarMensagem(mensagemFormulario, "Não foi possível carregar os modelos da marca selecionada.", "erro");
        }
    }

    function renderizarVeiculos() {
        const pesquisa = (campoPesquisa?.value || "").trim().toLocaleLowerCase("pt-BR");

        const filtrados = veiculos.filter(veiculo => {
            const conteudo = [
                obterPlaca(veiculo),
                obterCor(veiculo),
                obterNomeMarca(veiculo),
                obterNomeModelo(veiculo),
                obterNomeCliente(veiculo),
                ehMensalista(veiculo) ? "mensalista sim" : "mensalista não"
            ].join(" ").toLocaleLowerCase("pt-BR");

            return conteudo.includes(pesquisa);
        });

        listaVeiculos.replaceChildren();

        if (filtrados.length === 0) {
            const linha = document.createElement("tr");
            const celula = document.createElement("td");
            const icone = document.createElement("span");
            const titulo = document.createElement("strong");
            const descricao = document.createElement("span");

            celula.colSpan = 7;
            celula.className = "mensagem-vazia";
            icone.className = "mensagem-vazia-icone";
            icone.setAttribute("aria-hidden", "true");
            icone.textContent = "🚗";
            titulo.textContent = pesquisa ? "Nenhum veículo encontrado" : "Nenhum veículo cadastrado";
            descricao.textContent = pesquisa ? "Tente pesquisar usando outros termos." : "Clique em “Novo veículo” para cadastrar o primeiro.";

            celula.append(icone, titulo, descricao);
            linha.appendChild(celula);
            listaVeiculos.appendChild(linha);
            return;
        }

        filtrados.forEach(veiculo => {
            const linha = document.createElement("tr");
            const id = obterId(veiculo);

            linha.appendChild(criarCelula(obterPlaca(veiculo)));
            linha.appendChild(criarCelula(obterNomeMarca(veiculo)));
            linha.appendChild(criarCelula(obterNomeModelo(veiculo)));
            linha.appendChild(criarCelula(obterCor(veiculo)));
            linha.appendChild(criarCelula(obterNomeCliente(veiculo)));

            const celulaMensalista = document.createElement("td");
            const etiquetaMensalista = document.createElement("span");
            const mensalista = ehMensalista(veiculo);

            etiquetaMensalista.className = `situacao-veiculo ${mensalista ? "mensalista" : "nao-mensalista"}`;
            etiquetaMensalista.textContent = mensalista ? "Sim" : "Não";
            celulaMensalista.appendChild(etiquetaMensalista);
            linha.appendChild(celulaMensalista);

            const celulaAcoes = document.createElement("td");
            const acoes = document.createElement("div");
            acoes.className = "acoes-veiculo";

            acoes.appendChild(criarBotaoAcao(
                "Editar",
                "",
                editarVeiculo,
                id,
                `Editar veículo ${obterPlaca(veiculo)}`
            ));

            if (veiculoAtivo(veiculo)) {
                acoes.appendChild(criarBotaoAcao(
                    "Desativar",
                    "excluir",
                    desativarVeiculo,
                    id,
                    `Desativar veículo ${obterPlaca(veiculo)}`
                ));
            }

            celulaAcoes.appendChild(acoes);
            linha.appendChild(celulaAcoes);
            listaVeiculos.appendChild(linha);
        });
    }

    async function carregarVeiculos() {
        if (carregando) return;

        carregando = true;
        listaVeiculos.innerHTML = `
            <tr>
                <td colspan="7" class="mensagem-vazia">
                    <strong>Carregando veículos...</strong>
                    <span>Aguarde enquanto consultamos os cadastros.</span>
                </td>
            </tr>
        `;
        mostrarMensagem(mensagemLista, "");

        try {
            const dados = await requisicaoAPI(API_VEICULOS);
            veiculos = obterLista(dados, "veiculos");
            renderizarVeiculos();
        } catch (erro) {
            console.error("Erro ao carregar veículos:", erro);
            listaVeiculos.innerHTML = `
                <tr>
                    <td colspan="7" class="mensagem-vazia">
                        <strong>Não foi possível carregar os veículos.</strong>
                        <span>Verifique a conexão com o servidor e as rotas da API.</span>
                    </td>
                </tr>
            `;
            mostrarMensagem(mensagemLista, erro.message, "erro");
        } finally {
            carregando = false;
        }
    }

    async function abrirFormulario(veiculo = null) {
        formulario.reset();
        campoId.value = veiculo ? String(obterId(veiculo) ?? "") : "";
        mostrarMensagem(mensagemFormulario, "");

        await Promise.all([carregarClientes(), carregarMarcas()]);

        if (veiculo) {
            campoPlaca.value = obterPlaca(veiculo);
            campoCor.value = obterCor(veiculo);
            campoCliente.value = String(obterClienteId(veiculo) ?? "");
            campoMensalista.value = ehMensalista(veiculo) ? "sim" : "nao";

            const idMarca = obterMarcaId(veiculo);
            campoMarca.value = String(idMarca ?? "");
            await carregarModelos(idMarca, obterModeloId(veiculo));

            tituloFormulario.textContent = "Editar veículo";
            botaoSalvar.textContent = "Salvar alterações";
        } else {
            tituloFormulario.textContent = "Cadastrar veículo";
            botaoSalvar.textContent = "Salvar veículo";
            campoModelo.disabled = true;
        }

        painelFormulario.hidden = false;
        campoPlaca.focus();
        painelFormulario.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function fecharFormulario() {
        formulario.reset();
        campoId.value = "";
        campoModelo.disabled = true;
        painelFormulario.hidden = true;
        mostrarMensagem(mensagemFormulario, "");
    }

    function editarVeiculo(id) {
        const veiculo = veiculos.find(item => String(obterId(item)) === String(id));

        if (!veiculo) {
            mostrarMensagem(mensagemLista, "O veículo selecionado não foi encontrado.", "erro");
            return;
        }

        abrirFormulario(veiculo);
    }

    async function salvarVeiculo(evento) {
        evento.preventDefault();

        const placa = campoPlaca.value.trim().toUpperCase();
        const cor = campoCor.value;
        const idModelo = campoModelo.value;
        const idCliente = campoCliente.value;
        const id = campoId.value.trim();

        if (!placa || !cor || !idModelo || !idCliente) {
            mostrarMensagem(mensagemFormulario, "Preencha a placa, a cor, o modelo e o cliente responsável.", "erro");
            return;
        }

        if (!/^[A-Z]{3}(?:[0-9]{4}|[0-9][A-Z0-9][0-9]{2})$/.test(placa)) {
            mostrarMensagem(mensagemFormulario, "Informe uma placa válida. Exemplos: ABC1234 ou ABC1D23.", "erro");
            campoPlaca.focus();
            return;
        }

        const dados = {
            id_clients: Number(idCliente),
            id_modelo: Number(idModelo),
            placa,
            cor
        };

        const editando = Boolean(id);
        const url = editando ? `${API_VEICULOS}/${encodeURIComponent(id)}` : API_VEICULOS;

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
                editando ? "Veículo atualizado com sucesso." : "Veículo cadastrado com sucesso.",
                "sucesso"
            );

            await carregarVeiculos();
        } catch (erro) {
            console.error("Erro ao salvar veículo:", erro);
            mostrarMensagem(mensagemFormulario, erro.message || "Não foi possível salvar o veículo.", "erro");
        } finally {
            botaoSalvar.disabled = false;
            botaoSalvar.textContent = campoId.value ? "Salvar alterações" : "Salvar veículo";
        }
    }

    async function desativarVeiculo(id) {
        const veiculo = veiculos.find(item => String(obterId(item)) === String(id));

        if (!veiculo) {
            mostrarMensagem(mensagemLista, "O veículo selecionado não foi encontrado.", "erro");
            return;
        }

        const confirmado = window.confirm(`Deseja realmente desativar o veículo "${obterPlaca(veiculo)}"?`);
        if (!confirmado) return;

        mostrarMensagem(mensagemLista, "");

        try {
            await requisicaoAPI(`${API_VEICULOS}/${encodeURIComponent(id)}`, {
                method: "DELETE"
            });

            mostrarMensagem(mensagemLista, "Veículo desativado com sucesso.", "sucesso");
            await carregarVeiculos();
        } catch (erro) {
            console.error("Erro ao desativar veículo:", erro);
            mostrarMensagem(mensagemLista, erro.message || "Não foi possível desativar o veículo.", "erro");
        }
    }

    botaoNovo?.addEventListener("click", () => abrirFormulario());
    botaoCancelar?.addEventListener("click", fecharFormulario);
    formulario.addEventListener("submit", salvarVeiculo);
    campoPesquisa?.addEventListener("input", renderizarVeiculos);

    campoMarca?.addEventListener("change", () => {
        carregarModelos(campoMarca.value);
    });

    carregarVeiculos();
});