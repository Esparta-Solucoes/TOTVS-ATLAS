"""
Rotas da API para operações de embedding e busca vetorial.

Endpoints para gerenciar o ciclo de vida dos dados vetorizados, incluindo:
- Carga e vetorização de dados
- Busca por similaridade com filtros
- Gerenciamento de collection e índices
- Verificação e exclusão de pontos
"""

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
    description="""
    Inicia o processo completo de ETL: conecta ao banco, prepara os dados e os armazena no Qdrant.
    
    **Exemplo de uso**:
    ```bash
    curl -X POST "http://localhost:8000/api/embed-data" -H "accept: application/json"
    ```
    """
)
def trigger_embedding_process():
    """
    Endpoint para iniciar o processo completo de ETL e vetorização.
    
    Fluxo: conecta ao banco → carrega dados → prepara → vetoriza → armazena no Qdrant
    
    Returns:
        dict: Informações sobre o resultado do processamento
        
    Raises:
        HTTPException: Em caso de erro no processo
    """
    try:
        # Obter conexão com o banco
        db_engine = database.get_db_connection()
        if db_engine is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao conectar ao banco de dados. Verifique as credenciais e conexão."
            )
        
        # Carregar e preparar dados
        consolidated_df = etl.load_and_prepare_data(db_engine)
        if consolidated_df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Nenhum dado encontrado no banco de dados."
            )
        
        # Vetorizar e armazenar no Qdrant
        qdrant.embed_and_store_data(consolidated_df)
        
        return {
            "status": "success",
            "message": "Processo de vetorização concluído!",
            "collection_name": QDRANT_COLLECTION_NAME,
            "documents_processed": len(consolidated_df)
        }
    except HTTPException:
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
    description="""
    Realiza uma busca vetorial na coleção usando uma query de texto, filtrando por código do cliente.
    
    **Exemplo de uso**:
    ```bash
    curl -X GET "http://localhost:8000/api/search?query=problemas%20com%20faturamento&cd_cliente=123456&top_k=5" -H "accept: application/json"
    ```
    """
)
def search_in_vector_store(
    query: str = Query(..., description="Texto da consulta para busca por similaridade"),
    cd_cliente: str = Query(..., description="Código do cliente para filtrar os resultados"),
    top_k: int = Query(5, description="Número máximo de resultados a retornar")
):
    """
    Endpoint para busca semântica vetorial com filtro por cliente.
    
    Args:
        query: Texto da consulta para busca semântica
        cd_cliente: Código do cliente para filtrar resultados
        top_k: Quantidade máxima de resultados
        
    Returns:
        dict: Resultados da busca semântica
        
    Raises:
        HTTPException: Em caso de parâmetros inválidos ou erro na busca
    """
    if not query or query.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="O parâmetro 'query' não pode ser vazio."
        )
    
    if not cd_cliente or cd_cliente.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="O parâmetro 'cd_cliente' não pode ser vazio."
        )
    
    try:
        # Validar parâmetros
        if top_k < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O parâmetro 'top_k' deve ser um número positivo."
            )
            
        # Realizar busca vetorial com filtro
        results = qdrant.search_vectors(query, cd_cliente, top_k)
        
        return {
            "status": "success",
            "query": query,
            "cd_cliente": cd_cliente,
            "results_count": len(results),
            "results": results
        }
    except HTTPException:
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
    description="""
    Remove pontos da coleção Qdrant baseado em um campo e lista de valores específicos.
    
    **Exemplo de uso**:
    ```bash
    curl -X DELETE "http://localhost:8000/api/delete-points?field=cd_cliente&values=123456&values=789012" -H "accept: application/json"
    ```
    """
)
def delete_points_from_qdrant(
    field: str = Query(..., description="Campo a ser usado para filtrar (ex: 'cd_cliente', 'cd_produto')"),
    values: List[str] = Query(..., description="Lista de valores para filtrar")
):
    """
    Endpoint para remoção de pontos da collection por filtro.
    
    Args:
        field: Campo para filtrar (ex: cd_cliente)
        values: Lista de valores para o filtro
        
    Returns:
        dict: Resumo da operação de exclusão
        
    Raises:
        HTTPException: Em caso de parâmetros inválidos ou erro na exclusão
    """
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
        # Executar deleção
        deleted_values, failed_values = qdrant.delete_points_by_filter(field, values)
        
        # Preparar resposta
        response = {
            "status": "success" if len(failed_values) == 0 else "partial_success",
            "message": f"{len(deleted_values)} valores processados com sucesso, {len(failed_values)} falharam.",
            "collection_name": QDRANT_COLLECTION_NAME,
            "deleted_values": deleted_values,
            "failed_values": failed_values
        }
        
        # Atualizar status se tudo falhou
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
    description="""
    Cria um índice para o campo cd_cliente na coleção Qdrant para melhorar a performance das consultas.
    
    **Exemplo de uso**:
    ```bash
    curl -X POST "http://localhost:8000/api/create-index" -H "accept: application/json"
    ```
    """
)
def create_client_index():
    """
    Endpoint para criação de índice de cd_cliente no Qdrant.
    
    Returns:
        dict: Resultado da operação
        
    Raises:
        HTTPException: Em caso de erro na criação do índice
    """
    try:
        # Criar índice
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
    description="""
    Verifica se existem pontos no Qdrant com um determinado valor em um campo específico.
    
    **Exemplo de uso**:
    ```bash
    curl -X GET "http://localhost:8000/api/check-exists?field=cd_cliente&value=123456" -H "accept: application/json"
    ```
    """
)
def check_exists_in_qdrant(
    field: str = Query(..., description="Campo a verificar (ex: 'cd_cliente')"),
    value: str = Query(..., description="Valor a procurar")
):
    """
    Endpoint para verificar existência de pontos com valor específico.
    
    Args:
        field: Campo para verificar (ex: cd_cliente)
        value: Valor a ser procurado
        
    Returns:
        dict: Resultado da verificação
        
    Raises:
        HTTPException: Em caso de parâmetros inválidos ou erro na verificação
    """
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
        # Verificar existência
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
    description="""
    Cria uma collection Qdrant otimizada com configurações para melhor performance.
    
    **Exemplo de uso**:
    ```bash
    curl -X POST "http://localhost:8000/api/create-collection?recreate=true" -H "accept: application/json"
    ```
    """
)
def create_qdrant_collection(recreate: bool = Query(False, description="Se True, recria a collection mesmo se já existir.")):
    """
    Endpoint para criar collection Qdrant otimizada.
    
    Args:
        recreate: Se True, recria a collection mesmo se já existir
        
    Returns:
        dict: Resultado da operação
        
    Raises:
        HTTPException: Em caso de erro na criação da collection
    """
    try:
        # Criar collection otimizada
        success = qdrant.create_optimized_collection(recreate=recreate)
        
        if success:
            # Criar índice para cd_cliente
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
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"ERRO durante a criação da collection: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na criação da collection: {str(e)}. Verifique os logs para mais detalhes."
        )