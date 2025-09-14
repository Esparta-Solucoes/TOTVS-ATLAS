"""
Configurações da aplicação e integrações.

Este módulo centraliza todas as variáveis de configuração,
permitindo fácil ajuste e manutenção de parâmetros.
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Banco de Dados
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Configurações do Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Configurações do Modelo de Embedding
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
VECTOR_SIZE = 1024  # Tamanho do vetor para multilingual-e5-large

# Configurações da Vector Store
QDRANT_COLLECTION_NAME = "totvs_atlas_collection"