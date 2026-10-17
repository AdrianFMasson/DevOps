
const formulario = document.getElementById("formulario-login");
const campoEmail = document.getElementById("email");
const campoSenha = document.getElementById("senha");
const botaoVisualizar = document.getElementById("alternar-senha");
const botaoEntrar = formulario.querySelector(".botao-entrar");
const mensagem = document.getElementById("mensagem-login");

botaoVisualizar.addEventListener("click", () => {
    const mostrar = campoSenha.type === "password";
    campoSenha.type = mostrar ? "text" : "password";
    botaoVisualizar.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
    botaoVisualizar.setAttribute("aria-pressed", String(mostrar));
});

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    mensagem.textContent = "";
    botaoEntrar.disabled = true;

    try {
        const resposta = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                usuario: campoEmail.value.trim(),
                senha: campoSenha.value
            })
        });

        const resultado = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            mensagem.textContent = typeof resultado.detail === "string"
                ? resultado.detail
                : "Não foi possível realizar o login. Verifique os dados e tente novamente.";
            return;
        }

        if (!resultado.url) {
            mensagem.textContent = "O servidor não informou a página de destino.";
            return;
        }

        window.location.assign(resultado.url);
    } catch {
        mensagem.textContent = "Não foi possível conectar ao servidor. Tente novamente.";
    } finally {
        botaoEntrar.disabled = false;
    }
});
