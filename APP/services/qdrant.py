"""
Módulo de integração com o Qdrant para gerenciamento de embeddings e busca vetorial.

Este módulo implementa a inicialização lazy dos clientes pesados (modelos de embedding e
cliente Qdrant) para economizar recursos durante a inicialização da aplicação.
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
import uuid
import traceback

from APP.core import config
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain.schema.document import Document
from qdrant_client import QdrantClient, models
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue, FilterSelector, PointStruct

# Variáveis para inicialização lazy dos clientes
_embeddings_model = None
_qdrant_native_client = None

def get_embeddings_model():
    """
    Retorna uma instância do modelo de embeddings, inicializando-o se necessário.
    
    Returns:
        HuggingFaceEmbeddings: Instância do modelo de embeddings.
    """
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'trust_remote_code': True}
        )
    return _embeddings_model


def get_qdrant_client():
    """
    Retorna uma instância do cliente Qdrant, inicializando-o se necessário.
    
    Returns:
        QdrantClient: Instância do cliente Qdrant.
    """
    global _qdrant_native_client
    if _qdrant_native_client is None:
        _qdrant_native_client = QdrantClient(
            url=config.QDRANT_URL, 
            api_key=config.QDRANT_API_KEY,
            timeout=60
        )
    return _qdrant_native_client


def create_optimized_collection(recreate=False):
    """
    Cria uma collection Qdrant otimizada com configurações para melhor performance.
    
    Args:
        recreate (bool): Se True, recria a collection mesmo se já existir.
                         Se False, mantém a collection existente.
    
    Returns:
        bool: True se a collection foi criada/já existia, False em caso de erro.
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    try:
        # Verifica se a coleção já existe
        collections = get_qdrant_client().get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name in collection_names:
            if recreate:
                print(f"Removendo coleção existente '{collection_name}' para recriá-la...")
                get_qdrant_client().delete_collection(collection_name=collection_name)
            else:
                print(f"Coleção '{collection_name}' já existe. Não será recriada.")
                return True
        
        print(f"Criando coleção otimizada '{collection_name}'...")
        
        # Cria a collection com configurações otimizadas para performance e economia de RAM
        get_qdrant_client().create_collection(
            collection_name=collection_name,
            on_disk_payload=True,  # Armazena payloads no disco
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=0  # Reduz a quantidade de atualizações do índice
            ),
            vectors_config={
                "default": models.VectorParams(  # Nome "default" para compatibilidade com LangChain
                    size=config.VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                    on_disk=True,  # Armazena vetores no disco
                )
            },
        )
        
        print(f"Coleção '{collection_name}' criada com sucesso.")
        return True
    
    except Exception as e:
        print(f"ERRO ao criar coleção '{collection_name}': {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return False


def add_documents_directly(documents: List[Document], batch_size: int = 10):
    """
    Adiciona documentos diretamente usando o cliente nativo do Qdrant.
    
    Processa os documentos em lotes pequenos e tenta recuperar em caso de falha,
    processando documentos individualmente quando necessário.
    
    Args:
        documents (List[Document]): Lista de documentos LangChain a serem adicionados.
        batch_size (int): Tamanho do lote para processamento em massa.
    
    Returns:
        Tuple[int, int]: (total_success, total_failed) - Contagem de sucessos e falhas.
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    total_success = 0
    total_failed = 0
    
    # Processa em lotes para economizar memória
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        points = []
        
        try:
            # Prepara os pontos para este lote
            for doc in batch:
                embeddings = get_embeddings_model().embed_query(doc.page_content)
                point = PointStruct(
                    id=str(uuid.uuid4()),  # ID único
                    vector={"default": embeddings},  # Nome "default" para compatibilidade
                    payload=doc.metadata
                )
                points.append(point)
            
            # Insere os pontos no Qdrant
            get_qdrant_client().upsert(
                collection_name=collection_name,
                points=points
            )
            
            total_success += len(batch)
            print(f"Lote {i//batch_size + 1} processado: {len(batch)} documentos.")
            
        except Exception as e:
            total_failed += len(batch)
            print(f"ERRO no lote {i//batch_size + 1}: {str(e)}")
            
            # Se falhar o lote, tenta processar documento por documento
            if batch_size > 1:
                print(f"Tentando processar documentos individualmente...")
                for idx, doc in enumerate(batch):
                    try:
                        embeddings = get_embeddings_model().embed_query(doc.page_content)
                        point = PointStruct(
                            id=str(uuid.uuid4()),
                            vector={"default": embeddings},
                            payload=doc.metadata
                        )
                        
                        get_qdrant_client().upsert(
                            collection_name=collection_name,
                            points=[point]
                        )
                        
                        total_success += 1
                        total_failed -= 1
                        print(f"Documento {idx+1}/{len(batch)} processado individualmente.")
                    except Exception as e2:
                        print(f"ERRO no documento {idx+1}/{len(batch)}: {str(e2)}")
    
    return total_success, total_failed
def create_client_id_index():
    """
    Cria um índice para o campo 'cd_cliente' na coleção Qdrant.
    
    O índice melhora significativamente a performance das consultas filtradas 
    por código de cliente.
    
    Returns:
        bool: True se o índice foi criado com sucesso, False caso contrário.
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    try:
        print(f"Criando índice para 'cd_cliente' na coleção '{collection_name}'...")
        
        # Verifica se a coleção existe
        collections = get_qdrant_client().get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            print(f"A coleção '{collection_name}' não existe. Impossível criar índice.")
            return False
        
        # Cria o índice para o campo cd_cliente
        get_qdrant_client().create_payload_index(
            collection_name=collection_name,
            field_name="cd_cliente",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        print(f"Índice para 'cd_cliente' criado com sucesso.")
        return True
    except Exception as e:
        print(f"ERRO ao criar índice para 'cd_cliente': {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return False


def delete_points_by_filter(filter_field: str, filter_values: List[Any]) -> Tuple[List[Any], List[Any]]:
    """
    Remove pontos da coleção Qdrant baseados em um filtro de campo-valor.
    
    Args:
        filter_field (str): Campo de metadados para filtrar (ex: 'cd_cliente')
        filter_values (List[Any]): Lista de valores a filtrar no campo
        
    Returns:
        Tuple[List[Any], List[Any]]: (valores_excluídos, valores_com_falha)
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    deleted_values = []
    failed_values = []
    
    try:
        # Verifica se a coleção existe
        collections = get_qdrant_client().get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            print(f"A coleção '{collection_name}' não existe. Impossível excluir pontos.")
            return [], filter_values
        
        # Processa cada valor individualmente
        for value in filter_values:
            try:
                # Cria filtro para o valor específico
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key=filter_field, 
                            match=MatchValue(value=value)
                        )
                    ]
                )
                
                # Conta pontos afetados
                count_result = get_qdrant_client().count(
                    collection_name=collection_name,
                    count_filter=filter_condition
                )
                
                # Exclui os pontos
                get_qdrant_client().delete(
                    collection_name=collection_name,
                    points_selector=FilterSelector(filter=filter_condition)
                )
                
                print(f"Removidos {count_result.count} pontos com '{filter_field}={value}'")
                deleted_values.append(value)
                
            except Exception as e:
                print(f"ERRO ao excluir pontos com '{filter_field}={value}': {str(e)}")
                failed_values.append(value)
        
        print(f"Exclusão concluída: {len(deleted_values)} sucessos, {len(failed_values)} falhas.")
        return deleted_values, failed_values
    
    except Exception as e:
        print(f"ERRO geral ao excluir pontos: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return [], filter_values


def check_if_exists_in_qdrant(field: str, value: Any) -> bool:
    """
    Verifica se existem pontos na coleção Qdrant com um determinado valor.
    
    Args:
        field (str): Campo a verificar (ex: 'cd_cliente')
        value (Any): Valor a procurar
        
    Returns:
        bool: True se existirem pontos correspondentes, False caso contrário
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    
    try:
        # Filtro para consulta
        filter_condition = Filter(
            must=[
                FieldCondition(
                    key=field, 
                    match=MatchValue(value=value)
                )
            ]
        )
        
        # Conta pontos com este valor
        result = get_qdrant_client().count(
            collection_name=collection_name,
            count_filter=filter_condition
        )
        
        return result.count > 0
    
    except Exception as e:
        print(f"ERRO ao verificar existência de '{field}={value}': {str(e)}")
        return False


def df_to_langchain_documents(df: pd.DataFrame) -> List[Document]:
    """
    Converte um DataFrame para documentos do LangChain.
    
    Args:
        df (pd.DataFrame): DataFrame a ser convertido
        
    Returns:
        List[Document]: Lista de documentos LangChain
    """
    documents = []
    
    for _, row in df.iterrows():
        # Cria uma string com o conteúdo da linha para vetorização
        page_content = " ".join([f"{col}: {val}" for col, val in row.items()])
        
        # Todos os campos da linha se tornam metadados
        metadata = row.astype(str).to_dict()
        documents.append(Document(page_content=page_content, metadata=metadata))
    return documents


def embed_and_store_data(df: pd.DataFrame):
    """
    Converte DataFrame para documentos e os armazena no Qdrant.
    
    Fluxo: converte dados → cria collection → cria índice → vetoriza e armazena em lotes.
    
    Args:
        df (pd.DataFrame): DataFrame com os dados a serem vetorizados
    
    Raises:
        Exception: Repassa exceções de processamento
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    print(f"Preparando para armazenar dados na coleção '{collection_name}'...")

    try:
        # 1. Converter DataFrame para documentos
        print("Convertendo DataFrame para documentos LangChain...")
        documents = df_to_langchain_documents(df)

        if not documents:
            print("Nenhum documento para ser vetorizado.")
            return

        print(f"Total de documentos a serem vetorizados: {len(documents)}")
        
        # 2. Verificar conexão com Qdrant
        print(f"Testando conexão com Qdrant em {config.QDRANT_URL}...")
        collections = get_qdrant_client().get_collections()
        print(f"Conexão bem-sucedida. Coleções: {[c.name for c in collections.collections]}")

        # 3. Criar/recriar collection
        print("Criando collection otimizada...")
        collection_created = create_optimized_collection(recreate=True)
        
        if not collection_created:
            print("Falha ao criar collection. Operação cancelada.")
            return
        
        # 4. Criar índice para cd_cliente
        print("Criando índice para 'cd_cliente'...")
        create_client_id_index()
        
        # 5. Processar documentos em lotes
        print("Iniciando vetorização e armazenamento...")
        
        batch_size = 50  # Tamanho do lote
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        print(f"Processando {len(documents)} documentos em {total_batches} lotes.")
        
        total_success = 0
        total_failed = 0
        
        # Processar em lotes
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(documents))
            batch = documents[start_idx:end_idx]
            
            print(f"Processando lote {i+1}/{total_batches} ({len(batch)} documentos)...")
            
            # Usar cliente nativo com lotes menores
            success, failed = add_documents_directly(batch, batch_size=5)
            total_success += success
            total_failed += failed
            
            print(f"Progresso: {total_success}/{len(documents)} documentos ({(i+1)/total_batches*100:.1f}%)")
            
            # Resumo parcial periódico
            if (i+1) % 20 == 0 or i == total_batches - 1:
                print(f"RESUMO: {total_success} sucessos, {total_failed} falhas.")
        
        print(f"Processamento concluído: {total_success} sucessos, {total_failed} falhas.")
        
    except Exception as e:
        print(f"ERRO ao processar documentos: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        raise


def search_vectors(query: str, cd_cliente: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Busca vetores similares no Qdrant usando a abstração do LangChain.
    Filtra os resultados por cd_cliente.
    
    Args:
        query: A consulta de texto para busca por similaridade
        cd_cliente: O código do cliente para filtrar os resultados
        top_k: Número máximo de resultados a retornar
    
    Returns:
        Lista de dicionários com os resultados formatados
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    print(f"Buscando vetores para query: '{query}', cd_cliente: '{cd_cliente}', top_k: {top_k}")

    try:
        # Gera o embedding para a query
        embedding_vector = get_embeddings_model().embed_query(query)
        
        # Cria um filtro para o cd_cliente específico
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="cd_cliente",
                    match=models.MatchValue(value=cd_cliente)
                )
            ]
        )
        
        # Usa o cliente nativo do Qdrant diretamente para maior confiabilidade
        search_response = get_qdrant_client().search(
            collection_name=collection_name,
            query_vector=models.NamedVector(
                name="default",
                vector=embedding_vector
            ),
            query_filter=filter_condition,
            limit=top_k,
            with_payload=True
        )
        
        # Formata os resultados
        formatted_results = []
        for point in search_response:
            formatted_results.append({
                "score": point.score,
                "payload": point.payload
            })
        
        print(f"Busca concluída. {len(formatted_results)} resultados encontrados.")
        return formatted_results
        
    except Exception as e:
        print(f"ERRO durante a busca vetorial: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        # Retorna lista vazia em caso de erro para não quebrar a aplicação
        return []