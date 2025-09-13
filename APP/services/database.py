import urllib
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from APP.core import config

def get_db_connection() -> Engine:
    """
    Cria e retorna uma engine de conexão com o banco de dados Azure SQL.
    """
    try:
        params = urllib.parse.quote_plus(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config.DB_SERVER};"
            f"DATABASE={config.DB_DATABASE};"
            f"UID={config.DB_USERNAME};"
            f"PWD={config.DB_PASSWORD}"
        )
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        
        with engine.connect() as connection:
            print("Conexão com o banco de dados Azure bem-sucedida!")
        
        return engine
        
    except Exception as e:
        print(f"ERRO ao conectar ao banco de dados: {e}")
        raise