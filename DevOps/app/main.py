
from fastapi import FastAPI

app = FastAPI(
    title="Sistema de Estacionamento",
    description="API para gerenciamento de estacionamento",
    version="1.0.0"
)

@app.get("/")
def inicio():
    return {"mensagem": "API do Sistema de Estacionamento funcionando!"}
