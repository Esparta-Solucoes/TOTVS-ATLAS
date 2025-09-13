import pandas as pd
from typing import List, Dict, Any

from APP.core import config
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from langchain.schema.document import Document
from qdrant_client import QdrantClient

# --- Inicialização Singleton ---
# Corrigido para usar a abstração do LangChain, conforme seu exemplo.
embeddings_model = HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL,
    model_kwargs={'trust_remote_code': True}
)

# Cliente Qdrant para operações de gerenciamento como verificar se a coleção existe
qdrant_native_client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)


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

    # 1. Converte o DataFrame para o formato que o LangChain espera
    documents = df_to_langchain_documents(df)

    if not documents:
        print("Nenhum documento para ser vetorizado.")
        return

    # 2. Usa o método `from_documents` do LangChain para fazer "mágica"
    # Ele cuida de:
    #   - Criar a coleção se não existir (force_recreate=True garante uma coleção limpa)
    #   - Gerar os embeddings para cada documento usando o modelo especificado
    #   - Armazenar os vetores e metadados no Qdrant
    Qdrant.from_documents(
        documents=documents,
        embedding=embeddings_model,
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
        collection_name=collection_name,
        force_recreate=True, # Garante que estamos sempre com os dados mais recentes
    )
    
    print(f"{len(documents)} documentos foram vetorizados e armazenados com sucesso em '{collection_name}'.")


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