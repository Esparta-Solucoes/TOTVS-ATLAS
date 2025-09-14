import pandas as pd
from typing import List, Dict, Any, Tuple
import uuid

from APP.core import config
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain.schema.document import Document
from qdrant_client import QdrantClient, models
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue, FilterSelector, PointStruct
import traceback

# --- Inicialização Singleton ---
# Corrigido para usar a abstração do LangChain, conforme seu exemplo.
embeddings_model = HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL,
    model_kwargs={'trust_remote_code': True}
)

# Cliente Qdrant para operações de gerenciamento como verificar se a coleção existe
qdrant_native_client = QdrantClient(
    url=config.QDRANT_URL, 
    api_key=config.QDRANT_API_KEY,
    timeout=60  # Timeout de 60 segundos para operações mais demoradas
)


def create_optimized_collection(recreate=False):
    """
    Cria uma collection Qdrant otimizada com configurações para melhor performance.
    
    Args:
        recreate: Se True, recria a collection mesmo se já existir.
                 Se False, retorna sem fazer nada caso a collection já exista.
    
    Returns:
        bool: True se a collection foi criada com sucesso ou já existia, False em caso de erro.
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    try:
        # Verifica se a coleção já existe
        collections = qdrant_native_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name in collection_names:
            if recreate:
                print(f"Removendo coleção existente '{collection_name}' para recriá-la...")
                qdrant_native_client.delete_collection(collection_name=collection_name)
            else:
                print(f"Coleção '{collection_name}' já existe. Não será recriada.")
                return True
        
        print(f"Criando coleção otimizada '{collection_name}'...")
        
        # Cria a collection com configurações otimizadas
        # IMPORTANTE: LangChain usa o nome do vetor como 'default' e não 'dense'
        qdrant_native_client.create_collection(
            collection_name=collection_name,
            # Armazena os payloads no disco para economizar RAM
            on_disk_payload=True,
            # Configura otimizações de indexação
            optimizers_config=models.OptimizersConfigDiff(
                # Define o limite para indexação, reduz a quantidade de atualizações do índice
                indexing_threshold=0
            ),
            # Configura o vetor denso para embeddings com nome 'default' para compatibilidade com LangChain
            vectors_config={
                "default": models.VectorParams(
                    size=config.VECTOR_SIZE,
                    distance=models.Distance.COSINE,
                    on_disk=True,  # Armazena vetores no disco para economizar RAM
                )
            },
        )
        
        print(f"Coleção '{collection_name}' criada com sucesso com configurações otimizadas.")
        return True
    
    except Exception as e:
        print(f"ERRO ao criar coleção '{collection_name}': {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return False


def add_documents_directly(documents: List[Document], batch_size: int = 10):
    """
    Adiciona documentos diretamente usando o cliente nativo do Qdrant, sem depender do LangChain.
    Útil como fallback quando o método do LangChain falha.
    
    Args:
        documents: Lista de documentos LangChain a serem adicionados
        batch_size: Tamanho do lote para processamento
    
    Returns:
        tuple: (total_success, total_failed)
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    total_success = 0
    total_failed = 0
    
    # Processa em mini-lotes para economizar memória
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        points = []
        
        try:
            # Prepara os pontos para este mini-lote
            for doc in batch:
                # Gera embedding para o texto do documento
                embeddings = embeddings_model.embed_query(doc.page_content)
                
                # Cria um ponto Qdrant com o embedding e os metadados
                point = PointStruct(
                    id=str(uuid.uuid4()),  # ID único
                    vector={"default": embeddings},  # Vetor de embedding com nome "default"
                    payload=doc.metadata   # Metadados do documento
                )
                points.append(point)
            
            # Insere os pontos no Qdrant
            qdrant_native_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            total_success += len(batch)
            print(f"Mini-lote {i//batch_size + 1} processado com sucesso: {len(batch)} documentos.")
            
        except Exception as e:
            total_failed += len(batch)
            print(f"ERRO ao processar mini-lote {i//batch_size + 1}: {str(e)}")
            
            # Se ocorrer um erro no lote inteiro, tenta processar documento por documento
            if batch_size > 1:
                print(f"Tentando processar documentos individualmente...")
                for idx, doc in enumerate(batch):
                    try:
                        embeddings = embeddings_model.embed_query(doc.page_content)
                        point = PointStruct(
                            id=str(uuid.uuid4()),
                            vector={"default": embeddings},
                            payload=doc.metadata
                        )
                        
                        qdrant_native_client.upsert(
                            collection_name=collection_name,
                            points=[point]
                        )
                        
                        total_success += 1
                        total_failed -= 1
                        print(f"Documento {idx+1}/{len(batch)} processado individualmente com sucesso.")
                    except Exception as e2:
                        print(f"ERRO ao processar documento {idx+1}/{len(batch)}: {str(e2)}")
    
    return total_success, total_failed
def create_client_id_index():
    """
    Cria um índice para o campo 'cd_cliente' na coleção do Qdrant para melhorar
    a performance das consultas baseadas neste campo.
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    try:
        print(f"Criando índice para o campo 'cd_cliente' na coleção '{collection_name}'...")
        
        # Verifica se a coleção existe
        collections = qdrant_native_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            print(f"A coleção '{collection_name}' não existe. Impossível criar índice.")
            return False
        
        # Cria o índice para o campo cd_cliente
        qdrant_native_client.create_payload_index(
            collection_name=collection_name,
            field_name="cd_cliente",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        
        print(f"Índice para 'cd_cliente' criado com sucesso na coleção '{collection_name}'.")
        return True
    except Exception as e:
        print(f"ERRO ao criar índice para 'cd_cliente': {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return False


def delete_points_by_filter(filter_field: str, filter_values: List[Any]) -> Tuple[List[Any], List[Any]]:
    """
    Remove pontos da coleção Qdrant baseados em um filtro de campo-valor.
    
    Args:
        filter_field: O campo de metadados para filtrar (ex: 'cd_cliente', 'cd_produto')
        filter_values: Lista de valores a serem filtrados no campo especificado
        
    Returns:
        Tupla contendo duas listas:
        - Lista de valores que foram excluídos com sucesso
        - Lista de valores que falharam ao serem excluídos
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    deleted_values = []
    failed_values = []
    
    try:
        # Verifica se a coleção existe
        collections = qdrant_native_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if collection_name not in collection_names:
            print(f"A coleção '{collection_name}' não existe. Impossível excluir pontos.")
            return [], filter_values
        
        # Processa cada valor individualmente para ter controle sobre sucessos/falhas
        for value in filter_values:
            try:
                # Cria um filtro para encontrar pontos com o valor específico
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key=filter_field, 
                            match=MatchValue(value=value)
                        )
                    ]
                )
                
                # Conta quantos pontos serão afetados (para logging)
                count_result = qdrant_native_client.count(
                    collection_name=collection_name,
                    count_filter=filter_condition
                )
                
                # Exclui os pontos que correspondem ao filtro
                qdrant_native_client.delete(
                    collection_name=collection_name,
                    points_selector=FilterSelector(filter=filter_condition)
                )
                
                print(f"Removidos {count_result.count} pontos com '{filter_field}={value}' da coleção '{collection_name}'")
                deleted_values.append(value)
                
            except Exception as e:
                print(f"ERRO ao excluir pontos com '{filter_field}={value}': {str(e)}")
                failed_values.append(value)
        
        print(f"Exclusão concluída. {len(deleted_values)} valores processados com sucesso, {len(failed_values)} falharam.")
        return deleted_values, failed_values
    
    except Exception as e:
        print(f"ERRO geral ao excluir pontos: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return [], filter_values


def check_if_exists_in_qdrant(field: str, value: Any) -> bool:
    """
    Verifica se existem pontos na coleção Qdrant com um determinado valor em um campo específico.
    
    Args:
        field: O campo a verificar (ex: 'cd_cliente')
        value: O valor a procurar
        
    Returns:
        True se existirem pontos correspondentes, False caso contrário
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    
    try:
        # Cria filtro para a consulta
        filter_condition = Filter(
            must=[
                FieldCondition(
                    key=field, 
                    match=MatchValue(value=value)
                )
            ]
        )
        
        # Verifica se existem pontos que correspondem ao filtro
        result = qdrant_native_client.count(
            collection_name=collection_name,
            count_filter=filter_condition
        )
        
        return result.count > 0
    
    except Exception as e:
        print(f"ERRO ao verificar existência de '{field}={value}' no Qdrant: {str(e)}")
        return False


def row_to_text(row: pd.Series) -> str:
    """Converte uma linha do DataFrame em um texto rico em contexto para o embedding."""
    return (
        f"Cliente do segmento '{row.get('ds_segmento', 'N/A')}' "
        f"e faturamento '{row.get('faixa_faturamento', 'N/A')}' "
        f"com contrato '{row.get('situacao_contrato', 'N/A')}' "
        f"comprou o produto '{row.get('ds_produto', 'N/A')}' da marca '{row.get('marca_sovis', 'N/A')}'. "
        f"Valor: R$ {row.get('vl_total', 0):.2f}. Desconto: R$ {row.get('vl_desconto', 0):.2f}. "
        f"Data: {row.get('dia', 'N/A')}/{row.get('mes', 'N/A')}/{row.get('ano', 'N/A')}. "
        f"Local: {row.get('uf', 'N/A')}, {row.get('pais', 'N/A')}. "
        f"NPS: {row.get('nota_NPS', 'não avaliado')}."
    ).replace("'", "")


def df_to_langchain_documents(df: pd.DataFrame) -> List[Document]:
    """Converte um DataFrame em uma lista de Documentos LangChain."""
    documents = []
    for _, row in df.iterrows():
        # O conteúdo da página é o texto que será vetorizado
        page_content = row_to_text(row)
        # Os metadados são todas as colunas originais, para consulta posterior
        metadata = row.astype(str).to_dict()
        documents.append(Document(page_content=page_content, metadata=metadata))
    return documents


def embed_and_store_data(df: pd.DataFrame):
    """
    Converte o DataFrame em documentos LangChain e os armazena no Qdrant,
    lidando com a criação e vetorização de forma integrada.
    """
    collection_name = config.QDRANT_COLLECTION_NAME
    print(f"Preparando para armazenar dados na coleção '{collection_name}'...")

    try:
        # 1. Converte o DataFrame para o formato que o LangChain espera
        print("Convertendo DataFrame para documentos LangChain...")
        documents = df_to_langchain_documents(df)

        if not documents:
            print("Nenhum documento para ser vetorizado.")
            return

        # Verificar tamanho dos documentos para diagnóstico
        print(f"Total de documentos a serem vetorizados: {len(documents)}")
        
        # Verificando a conexão com Qdrant antes de prosseguir
        print(f"Testando conexão com Qdrant em {config.QDRANT_URL}...")
        # Tenta uma operação simples para verificar conectividade
        collections = qdrant_native_client.get_collections()
        print(f"Conexão com Qdrant bem-sucedida. Coleções existentes: {[c.name for c in collections.collections]}")

        # 2. Cria a collection otimizada (ou recria se já existir)
        print("Criando/verificando collection otimizada...")
        collection_created = create_optimized_collection(recreate=True)
        
        if not collection_created:
            print("Falha ao criar collection. Operação de embedding cancelada.")
            return
        
        # 3. Após criar a collection, imediatamente cria o índice para cd_cliente
        print("Collection criada. Criando índice para 'cd_cliente'...")
        create_client_id_index()
        
        # 4. Usa processamento em lotes para inserir os documentos
        print("Iniciando processo de vetorização e armazenamento...")
        
        # Reduzir tamanho do lote para processamento mais confiável
        batch_size = 50  # Ainda menor para economizar memória
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        print(f"Processando {len(documents)} documentos em {total_batches} lotes de até {batch_size} documentos cada.")
        
        # Como sabemos que o LangChain está com problemas, vamos direto para o cliente nativo
        print("Utilizando cliente nativo do Qdrant para inserção direta...")
        
        total_success = 0
        total_failed = 0
        
        # Processa os documentos em lotes pequenos
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(documents))
            batch = documents[start_idx:end_idx]
            
            print(f"Processando lote {i+1}/{total_batches} ({len(batch)} documentos)...")
            
            # Em vez de tentar o LangChain primeiro, usa diretamente o cliente nativo
            # com um tamanho de batch menor
            success, failed = add_documents_directly(batch, batch_size=5)
            total_success += success
            total_failed += failed
            
            print(f"Progresso: {total_success}/{len(documents)} documentos inseridos com sucesso ({(i+1)/total_batches*100:.1f}% concluído)")
            
            # A cada 20 lotes, mostra um resumo
            if (i+1) % 20 == 0 or i == total_batches - 1:
                print(f"RESUMO PARCIAL: {total_success} documentos inseridos com sucesso, {total_failed} falhas.")
        
        print(f"Processamento concluído: {total_success} documentos inseridos com sucesso, {total_failed} falhas.")
        print(f"{len(documents)} documentos processados para inserção em '{collection_name}'.")
    except Exception as e:
        import traceback
        print(f"ERRO ao processar documentos: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        raise


def search_vectors(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Busca vetores similares no Qdrant usando a abstração do LangChain."""
    collection_name = config.QDRANT_COLLECTION_NAME

    # 1. Inicializa o cliente LangChain para a coleção existente
    qdrant_lc_client = Qdrant(
        client=qdrant_native_client,
        collection_name=collection_name,
        embeddings=embeddings_model
    )

    # 2. Realiza a busca por similaridade
    # Este método já cuida de vetorizar a query e comparar com os vetores na coleção
    search_results = qdrant_lc_client.similarity_search_with_score(query=query, k=top_k)

    # 3. Formata os resultados
    formatted_results = []
    for doc, score in search_results:
        formatted_results.append({
            "score": score,
            "payload": doc.metadata
        })
        
    return formatted_results