import pandas as pd
from sqlalchemy.engine import Engine

def load_and_prepare_data(engine: Engine) -> pd.DataFrame:
    """
    Carrega, une e prepara os dados do banco para vetorização.
    
    Processo: carrega tabelas → realiza joins → trata NPS → remove duplicados → preenche valores nulos
    
    Args:
        engine (Engine): Conexão SQLAlchemy com o banco de dados
        
    Returns:
        pd.DataFrame: DataFrame consolidado e tratado pronto para vetorização
    """
    print("Iniciando processo de ETL...")
    
    # Definição das tabelas a serem carregadas
    tabelas = [
        "Fato_Consumo", "Dim_Cliente", "Dim_Contrato", "Dim_Produto", "Dim_Nps",
        "Dim_Segmento", "Dim_Faturamento", "Dim_Localidade", "Dim_Modalidade",
        "Dim_StatusContrato", "Dim_Marca", "Dim_LinhaReceita", "Dim_Tempo"
    ]
    
    # Carregamento das tabelas
    dfs = {}
    with engine.connect() as conn:
        for tabela in tabelas:
            dfs[tabela] = pd.read_sql(f"SELECT * FROM {tabela}", conn)

    # Joins para criar dataframe consolidado
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
    
    # Tratamento especial para NPS
    if 'respondeAt' in dfs['Dim_Nps'].columns:
        print("Tratando dados de NPS e normalizando valores...")
        dfs['Dim_Nps']['respondeAt'] = pd.to_datetime(dfs['Dim_Nps']['respondeAt'])
        
        # Normalização dos valores de NPS para escala de 0-10
        if 'nps' in dfs['Dim_Nps'].columns:
            dfs['Dim_Nps']['nps'] = pd.to_numeric(dfs['Dim_Nps']['nps'], errors='coerce')
            
            # Normaliza valores na escala de dezenas para 0-10
            mask_dezenas = dfs['Dim_Nps']['nps'] > 10
            dfs['Dim_Nps'].loc[mask_dezenas, 'nps'] = dfs['Dim_Nps'].loc[mask_dezenas, 'nps'] / 10
            
            # Garante valores entre 0 e 10
            dfs['Dim_Nps']['nps'] = dfs['Dim_Nps']['nps'].clip(0, 10)
            
            print(f"NPS normalizado: {dfs['Dim_Nps']['nps'].min()} a {dfs['Dim_Nps']['nps'].max()}")
        
        # Usa apenas a resposta mais recente de NPS por cliente
        nps_recente = dfs['Dim_Nps'].sort_values('respondeAt').drop_duplicates('cd_cliente', keep='last')
        df = pd.merge(df, nps_recente, on='cd_cliente', how='left')
    
    # Remoção de registros duplicados
    print(f"Registros antes da deduplicação: {len(df)}")
    
    # Chaves para deduplicação (cliente+contrato+produto)
    chaves_deduplicacao = ['cd_cliente', 'cd_contrato', 'cd_produto']
    
    # Remove duplicados mantendo o registro mais recente
    if 'dt_consumo' in df.columns:
        df = df.sort_values('dt_consumo', ascending=False).drop_duplicates(subset=chaves_deduplicacao, keep='first')
    else:
        df = df.drop_duplicates(subset=chaves_deduplicacao, keep='first')
    
    print(f"Registros após deduplicação: {len(df)}")
    
    # Preenchimento de valores nulos
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('Não informado')
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
    
    print(f"ETL concluído. {len(df)} registros processados.")
    return df
