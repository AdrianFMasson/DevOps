
(() => {
    "use strict";

    // Preserva o fetch original para evitar que a renovação
    // da sessão entre em um ciclo de novas tentativas.
    const fetchOriginal = window.fetch.bind(window);

    let refreshPromise = null;
    let refreshVersion = 0;

    async function renovarSessao() {
        if (!refreshPromise) {
            refreshPromise = fetchOriginal("/api/refresh", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json"
                }
            })
                .then((response) => {
                    if (response.ok) {
                        refreshVersion++;
                        return true;
                    }

                    return false;
                })
                .catch((error) => {
                    console.error("Erro ao renovar a sessão:", error);
                    return false;
                })
                .finally(() => {
                    refreshPromise = null;
                });
        }

        return refreshPromise;
    }

    function isRotaAutenticacao(url) {
        return (
            url.includes("/api/login") ||
            url.includes("/api/refresh") ||
            url.includes("/api/logout")
        );
    }

    async function apiFetch(input, init = {}) {
        const request = new Request(input, {
            ...init,
            credentials: init.credentials ?? "same-origin"
        });

        const versaoInicial = refreshVersion;

        // Primeira tentativa.
        let response = await fetchOriginal(request.clone());

        if (response.status !== 401) {
            return response;
        }

        if (isRotaAutenticacao(request.url)) {
            return response;
        }

        // Outra requisição pode já ter renovado a sessão.
        // Nesse caso, não precisamos renovar novamente.
        if (versaoInicial === refreshVersion) {
            const renovacaoOk = await renovarSessao();

            if (!renovacaoOk) {
                window.location.replace("/");
                return response;
            }
        }

        // Repete a requisição original com os novos cookies.
        response = await fetchOriginal(request.clone());

        if (response.status === 401) {
            window.location.replace("/");
        }

        return response;
    }

    // Disponibiliza a função para todos os scripts das páginas.
    window.apiFetch = apiFetch;
})();
