import pandas as pd
from sqlalchemy.engine import Engine

def load_and_prepare_data(engine: Engine) -> pd.DataFrame:
    """
    Carrega, une e prepara os dados do banco para vetorização.
    """
    print("Iniciando processo de ETL...")
    tabelas = [
        "Fato_Consumo", "Dim_Cliente", "Dim_Contrato", "Dim_Produto", "Dim_Nps",
        "Dim_Segmento", "Dim_Faturamento", "Dim_Localidade", "Dim_Modalidade",
        "Dim_StatusContrato", "Dim_Marca", "Dim_LinhaReceita", "Dim_Tempo"
    ]
    dfs = {}
    with engine.connect() as conn:
        for tabela in tabelas:
            dfs[tabela] = pd.read_sql(f"SELECT * FROM {tabela}", conn)

    df = pd.merge(dfs['Fato_Consumo'], dfs['Dim_Cliente'], on='cd_cliente', how='left')
    df = pd.merge(df, dfs['Dim_Contrato'], on='cd_contrato', how='left')
    df = pd.merge(df, dfs['Dim_Produto'], on='cd_produto', how='left')
    df = pd.merge(df, dfs['Dim_Tempo'], on='cd_tempo', how='left')
    df = pd.merge(df, dfs['Dim_Segmento'], on='cd_segmento', how='left')
    df = pd.merge(df, dfs['Dim_Faturamento'], on='cd_faturamento', how='left')
    df = pd.merge(df, dfs['Dim_Localidade'], on='cd_localidade', how='left')
    df = pd.merge(df, dfs['Dim_StatusContrato'], on='cd_status', how='left')
    df = pd.merge(df, dfs['Dim_Modalidade'], on='cd_modalidade', how='left')
    df = pd.merge(df, dfs['Dim_Marca'], on='cd_marca', how='left')
    df = pd.merge(df, dfs['Dim_LinhaReceita'], on='cd_lin_rec', how='left')
    
    if 'respondeAt' in dfs['Dim_Nps'].columns:
        dfs['Dim_Nps']['respondeAt'] = pd.to_datetime(dfs['Dim_Nps']['respondeAt'])
        nps_recente = dfs['Dim_Nps'].sort_values('respondeAt').drop_duplicates('cd_cliente', keep='last')
        df = pd.merge(df, nps_recente, on='cd_cliente', how='left')
    
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col].fillna('Não informado', inplace=True)
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col].fillna(0, inplace=True)
    
    print(f"ETL concluído. {len(df)} registros processados.")
    return df
