import uvicorn
from fastapi import FastAPI
from APP.api import router as api_router
from APP.core.config import QDRANT_COLLECTION_NAME

# Cria a instância principal da aplicação FastAPI
app = FastAPI(
    title="API RAG com Banco de Dados e Qdrant",
    description=f"API para extrair, vetorizar dados e realizar buscas. Coleção ativa: '{QDRANT_COLLECTION_NAME}'",
    version="1.1.0",
)

# Inclui as rotas definidas no módulo da API. O prefixo /api é opcional, mas recomendado.
app.include_router(api_router.router, prefix="/api", tags=["RAG Service"])

@app.get("/", summary="Endpoint Raiz", description="Verifica o status da API.", tags=["Status"])
def read_root():
    """Endpoint raiz para verificar se a API está online."""
    return {"status": "API está online e funcionando!", "docs_url": "/docs"}

# Bloco para permitir a execução direta do servidor com 'python main.py'
if __name__ == "__main__":
    # O --reload é ótimo para desenvolvimento, pois reinicia o servidor a cada alteração no código.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)