from fastapi import APIRouter, HTTPException, status
from APP.services import database, etl, qdrant
from APP.core.config import QDRANT_COLLECTION_NAME

router = APIRouter()

@router.post(
    "/embed-data", 
    status_code=status.HTTP_201_CREATED,
    summary="Processa e Vetoriza os Dados do Banco",
    description="Inicia o processo completo de ETL: conecta ao banco, prepara os dados e os armazena no Qdrant."
)
def trigger_embedding_process():
    try:
        db_engine = database.get_db_connection()
        consolidated_df = etl.load_and_prepare_data(db_engine)
        if consolidated_df.empty:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Nenhum dado encontrado.")
        
        qdrant.embed_and_store_data(consolidated_df)
        return {
            "message": "Processo de vetorização concluído!",
            "collection_name": QDRANT_COLLECTION_NAME,
            "documents_processed": len(consolidated_df)
        }
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro no processo: {e}")

@router.get(
    "/search",
    summary="Busca por Similaridade no Qdrant",
    description="Realiza uma busca vetorial na coleção usando uma query de texto."
)
def search_in_vector_store(query: str, top_k: int = 5):
    if not query:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "'query' não pode ser vazio.")
    try:
        results = qdrant.search_vectors(query, top_k)
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro na busca: {e}")