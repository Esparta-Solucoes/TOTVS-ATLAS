import pandas as pd
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from APP.core import config

# Inicialização Singleton para performance
model = SentenceTransformer(config.EMBEDDING_MODEL)
qdrant_client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)

def row_to_text(row: pd.Series) -> str:
    """Converte uma linha do DataFrame em um texto rico em contexto."""
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

def embed_and_store_data(df: pd.DataFrame):
    """Vetoriza os dados e armazena no Qdrant."""
    vector_size = model.get_sentence_embedding_dimension()
    collection_name = config.QDRANT_COLLECTION_NAME

    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    
    payloads = df.to_dict(orient='records')
    texts_to_embed = [row_to_text(row) for row in payloads]
    vectors = model.encode(texts_to_embed, show_progress_bar=True)

    qdrant_client.upsert(
        collection_name=collection_name,
        points=models.Batch(
            ids=[i for i in range(len(payloads))], 
            vectors=vectors.tolist(),
            payloads=payloads
        ),
        wait=True
    )
    print(f"{len(payloads)} documentos armazenados em '{collection_name}'.")

def search_vectors(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Busca vetores similares no Qdrant."""
    query_vector = model.encode(query).tolist()
    search_result = qdrant_client.search(
        collection_name=config.QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True
    )
    return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in search_result]
