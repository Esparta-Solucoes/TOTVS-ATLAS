"""
Módulo principal da aplicação FastAPI para RAG com Banco de Dados e Qdrant.

Este módulo configura a aplicação FastAPI, registra as rotas API
e inicia o servidor de desenvolvimento quando executado diretamente.

**Exemplos de uso via curl**:

Verificar status da API:
```bash
curl -X GET "http://localhost:8000/" -H "accept: application/json"
```

Consultar documentação:
```bash
curl -X GET "http://localhost:8000/docs" -H "accept: application/json"
```
"""

import uvicorn
from fastapi import FastAPI
from APP.api import router as api_router
from APP.core.config import QDRANT_COLLECTION_NAME

# Criar instância FastAPI
app = FastAPI(
    title="API RAG com Banco de Dados e Qdrant",
    description=f"API para extrair, vetorizar dados e realizar buscas. Coleção ativa: '{QDRANT_COLLECTION_NAME}'",
    version="1.1.0",
)

# Incluir rotas API
app.include_router(api_router.router, prefix="/api", tags=["RAG Service"])

@app.get("/", summary="Endpoint Raiz", description="Verifica o status da API.", tags=["Status"])
def read_root():
    """
    Endpoint raiz para verificar se a API está online.
    
    Returns:
        dict: Status da API e URL da documentação
    """
    return {"status": "API está online e funcionando!", "docs_url": "/docs"}

# Execução como script
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)