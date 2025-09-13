import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações do Banco de Dados ---
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- Configurações do Qdrant ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# --- Configurações do Modelo de Embedding ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# --- Configurações da Vector Store ---
QDRANT_COLLECTION_NAME = "consumo_clientes_db_v2"