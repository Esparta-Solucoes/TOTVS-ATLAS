from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Any
from APP.services import database, etl, qdrant
from APP.core.config import QDRANT_COLLECTION_NAME
import traceback

router = APIRouter()

@router.post(
    "/embed-data", 
    status_code=status.HTTP_201_CREATED,
    summary="Processa e Vetoriza os Dados do Banco",
    description="Inicia o processo completo de ETL: conecta ao banco, prepara os dados e os armazena no Qdrant."
)
def trigger_embedding_process():
    try:
        # Obter conexão com o banco de dados
        db_engine = database.get_db_connection()
        if db_engine is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao conectar ao banco de dados. Verifique as credenciais e conexão."
            )
        
        # Carregar e preparar os dados
        consolidated_df = etl.load_and_prepare_data(db_engine)
        if consolidated_df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Nenhum dado encontrado no banco de dados."
            )
        
        # Armazenar os dados no Qdrant
        # O índice para cd_cliente será criado automaticamente dentro desta função
        qdrant.embed_and_store_data(consolidated_df)
        
        return {
            "status": "success",
            "message": "Processo de vetorização concluído!",
            "collection_name": QDRANT_COLLECTION_NAME,
            "documents_processed": len(consolidated_df)
        }
    except HTTPException:
        # Repassa exceções HTTP já formatadas
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO durante o processo de embedding: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro no processo de embedding: {str(e)}. Verifique os logs para mais detalhes."
        )

@router.get(
    "/search",
    summary="Busca por Similaridade no Qdrant",
    description="Realiza uma busca vetorial na coleção usando uma query de texto."
)
def search_in_vector_store(query: str, top_k: int = 5):
    if not query or query.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="O parâmetro 'query' não pode ser vazio."
        )
    
    try:
        # Validação de parâmetros
        if top_k < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O parâmetro 'top_k' deve ser um número positivo."
            )
            
        # Realiza a busca vetorial
        results = qdrant.search_vectors(query, top_k)
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": results
        }
    except HTTPException:
        # Repassa exceções HTTP já formatadas
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO durante a busca vetorial: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro na busca vetorial: {str(e)}. Verifique os logs para mais detalhes."
        )


@router.delete(
    "/delete-points",
    status_code=status.HTTP_200_OK,
    summary="Remove Pontos do Qdrant por Filtro",
    description="Remove pontos da coleção Qdrant baseado em um campo e lista de valores específicos."
)
def delete_points_from_qdrant(
    field: str = Query(..., description="Campo a ser usado para filtrar (ex: 'cd_cliente', 'cd_produto')"),
    values: List[str] = Query(..., description="Lista de valores para filtrar")
):
    if not field or field.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O parâmetro 'field' não pode ser vazio."
        )
    
    if not values or len(values) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O parâmetro 'values' deve conter pelo menos um valor."
        )
    
    try:
        # Executa a deleção dos pontos
        deleted_values, failed_values = qdrant.delete_points_by_filter(field, values)
        
        # Prepara a resposta
        response = {
            "status": "success" if len(failed_values) == 0 else "partial_success",
            "message": f"{len(deleted_values)} valores processados com sucesso, {len(failed_values)} falharam.",
            "collection_name": QDRANT_COLLECTION_NAME,
            "deleted_values": deleted_values,
            "failed_values": failed_values
        }
        
        # Se todos os valores falharam, altera o status da resposta
        if len(deleted_values) == 0 and len(failed_values) > 0:
            response["status"] = "error"
            response["message"] = "Falha ao excluir todos os pontos solicitados."
        
        return response
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO durante a exclusão de pontos: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na exclusão de pontos: {str(e)}. Verifique os logs para mais detalhes."
        )


@router.post(
    "/create-index",
    status_code=status.HTTP_201_CREATED,
    summary="Cria Índice para Campo cd_cliente",
    description="Cria um índice para o campo cd_cliente na coleção Qdrant para melhorar a performance das consultas."
)
def create_client_index():
    try:
        # Tenta criar o índice
        success = qdrant.create_client_id_index()
        
        if success:
            return {
                "status": "success",
                "message": "Índice para o campo 'cd_cliente' criado com sucesso.",
                "collection_name": QDRANT_COLLECTION_NAME
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao criar índice para o campo 'cd_cliente'. Verifique os logs para mais detalhes."
            )
    
    except HTTPException:
        # Repassa exceções HTTP já formatadas
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO durante a criação do índice: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na criação do índice: {str(e)}. Verifique os logs para mais detalhes."
        )


@router.get(
    "/check-exists",
    status_code=status.HTTP_200_OK,
    summary="Verifica Existência no Qdrant",
    description="Verifica se existem pontos no Qdrant com um determinado valor em um campo específico."
)
def check_exists_in_qdrant(
    field: str = Query(..., description="Campo a verificar (ex: 'cd_cliente')"),
    value: str = Query(..., description="Valor a procurar")
):
    if not field or field.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O parâmetro 'field' não pode ser vazio."
        )
    
    if not value or value.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O parâmetro 'value' não pode ser vazio."
        )
    
    try:
        # Verifica se o valor existe
        exists = qdrant.check_if_exists_in_qdrant(field, value)
        
        return {
            "status": "success",
            "exists": exists,
            "field": field,
            "value": value,
            "collection_name": QDRANT_COLLECTION_NAME
        }
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO ao verificar existência: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar existência: {str(e)}. Verifique os logs para mais detalhes."
        )


@router.post(
    "/create-collection",
    status_code=status.HTTP_201_CREATED,
    summary="Cria Collection Qdrant Otimizada",
    description="Cria uma collection Qdrant otimizada com configurações para melhor performance."
)
def create_qdrant_collection(recreate: bool = Query(False, description="Se True, recria a collection mesmo se já existir.")):
    try:
        # Tenta criar a collection otimizada
        success = qdrant.create_optimized_collection(recreate=recreate)
        
        if success:
            # Se a collection foi criada com sucesso, também cria o índice
            index_created = qdrant.create_client_id_index()
            
            return {
                "status": "success",
                "message": "Collection Qdrant criada com sucesso com configurações otimizadas.",
                "collection_name": QDRANT_COLLECTION_NAME,
                "index_created": index_created
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao criar collection Qdrant. Verifique os logs para mais detalhes."
            )
    
    except HTTPException:
        # Repassa exceções HTTP já formatadas
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO durante a criação da collection: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na criação da collection: {str(e)}. Verifique os logs para mais detalhes."
        )