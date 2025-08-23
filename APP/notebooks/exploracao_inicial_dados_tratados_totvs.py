import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from io import StringIO
import urllib

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO DA CONEXÃO COM O BANCO DE DADOS AZURE ---
db_server = os.getenv("DB_SERVER")
db_database = os.getenv("DB_DATABASE")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")

# Verifica se as credenciais foram carregadas
if not all([db_server, db_database, db_username, db_password]):
    print("ERRO: Verifique se todas as variáveis de ambiente (DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD) estão no arquivo .env")
    exit()

# Monta a string de conexão para o SQL Server com pyodbc
params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={db_server};"
    f"DATABASE={db_database};"
    f"UID={db_username};"
    f"PWD={db_password}"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


# --- CONFIGURAÇÃO DA ANÁLISE ---

# Lista das tabelas a serem exploradas (baseado no seu diagrama)
tabelas_para_explorar = [
    "Fato_Consumo",
    "Dim_Cliente",
    "Dim_Contrato",
    "Dim_Produto",
    "Dim_Nps",
    "Dim_Segmento",
    "Dim_Faturamento",
    "Dim_Localidade",
    "Dim_Modalidade",
    "Dim_StatusContrato",
    "Dim_Tempo",
    "Dim_Marca",
    "Dim_LinhaReceita"
]

# Define o caminho do arquivo de saída na mesma pasta do script
arquivo_saida = os.path.join(os.path.dirname(__file__), "exploracao_output_dados_tratados.txt")


# --- FUNÇÕES DE ANÁLISE ---

def explorar_tabela(nome_tabela, conn, print_func=print):
    """
    Função aprimorada para conectar, ler uma tabela do banco de dados
    e realizar uma análise exploratória inicial.
    """
    print_func("="*100)
    print_func(f"TABELA: {nome_tabela.upper()}")
    
    try:
        # Lê a tabela inteira para um DataFrame do Pandas
        query = f"SELECT * FROM {nome_tabela}"
        df = pd.read_sql(query, conn)
    except Exception as e:
        print_func(f"ERRO ao ler a tabela {nome_tabela.upper()}: {e}")
        print_func("="*100 + "\n")
        return

    if df.empty:
        print_func("-> AVISO: A tabela está vazia.")
        print_func("="*100 + "\n")
        return

    print_func(f"-> Linhas: {df.shape[0]}, Colunas: {df.shape[1]}")
    print_func("-"*100)
    
    # Captura a saída de df.info() para um buffer
    print_func("INFO DO DATAFRAME:")
    buffer = StringIO()
    df.info(buf=buffer)
    print_func(buffer.getvalue())
    print_func("-"*100)
    
    print_func("COLUNAS:")
    print_func(df.columns.tolist())
    print_func("-"*100)
    
    print_func("PRIMEIRAS 5 LINHAS:")
    print_func(df.head().to_string())
    print_func("-"*100)

    print_func("VALORES NULOS POR COLUNA:")
    print_func(df.isnull().sum().to_string())
    print_func("-"*100)
    
    print_func("LINHAS DUPLICADAS:")
    print_func(df.duplicated().sum())
    print_func("-"*100)
    
    print_func("VALORES ÚNICOS POR COLUNA:")
    print_func(df.nunique().to_string())
    print_func("-"*100)

    # Estatísticas descritivas numéricas
    numeric_cols = df.select_dtypes(include='number').columns
    if len(numeric_cols) > 0:
        print_func("ESTATÍSTICAS DESCRITIVAS (NUMÉRICAS):")
        print_func(df[numeric_cols].describe().transpose().to_string())
    else:
        print_func("ESTATÍSTICAS DESCRITIVAS (NUMÉRICAS): Nenhuma coluna numérica encontrada.")
    print_func("-"*100)

    # Estatísticas descritivas categóricas/objetos
    object_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(object_cols) > 0:
        print_func("ESTATÍSTICAS DESCRITIVAS (CATEGÓRICAS):")
        print_func(df[object_cols].describe().transpose().to_string())
    else:
        print_func("ESTATÍSTICAS DESCRITIVAS (CATEGÓRICAS): Nenhuma coluna categórica encontrada.")
    print_func("-"*100)
    
    # Estatísticas de colunas de data
    date_cols = df.select_dtypes(include=['datetime64[ns]']).columns
    if len(date_cols) > 0:
        print_func("ESTATÍSTICAS DESCRITIVAS (DATAS):")
        for col in date_cols:
            print_func(f"  Coluna '{col}':")
            print_func(f"    Mínimo: {df[col].min()}")
            print_func(f"    Máximo: {df[col].max()}")
    else:
        print_func("ESTATÍSTICAS DESCRITIVAS (DATAS): Nenhuma coluna de data encontrada.")
    print_func("-"*100)

    print_func("="*100 + "\n")

def main():
    """
    Função principal para executar a análise em todas as tabelas e salvar o resultado.
    """
    try:
        # Tenta conectar ao banco de dados
        conn = engine.connect()
        print("Conexão com o banco de dados bem-sucedida!")
    except Exception as e:
        print(f"ERRO: Falha ao conectar ao banco de dados. Verifique suas credenciais e a string de conexão.\nDetalhes: {e}")
        return

    # Abre o arquivo de log para escrita
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        # Função para imprimir tanto no console quanto no arquivo
        def print_duplo(*args, **kwargs):
            print(*args, **kwargs)
            print(*args, **kwargs, file=f)

        # Itera sobre a lista de tabelas e executa a exploração
        for tabela in tabelas_para_explorar:
            explorar_tabela(tabela, conn, print_func=print_duplo)

    # Fecha a conexão com o banco
    conn.close()
    print(f"\nAnálise concluída. Resultados salvos em: '{os.path.abspath(arquivo_saida)}'")


if __name__ == "__main__":
    main()