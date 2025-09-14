import pandas as pd
from sqlalchemy.engine import Engine

def load_and_prepare_data(engine: Engine) -> pd.DataFrame:
    """
    Carrega, une e prepara os dados do banco para vetorização.
    Inclui remoção de duplicados e normalização de valores NPS.
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

    # Realizando os joins para criar o dataframe consolidado
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
    
    # Tratamento especial para os dados de NPS
    if 'respondeAt' in dfs['Dim_Nps'].columns:
        print("Tratando dados de NPS e normalizando valores...")
        dfs['Dim_Nps']['respondeAt'] = pd.to_datetime(dfs['Dim_Nps']['respondeAt'])
        
        # Normalização dos valores de NPS para escala de 0-10
        if 'nps' in dfs['Dim_Nps'].columns:
            # Converte para numérico, tratando possíveis erros
            dfs['Dim_Nps']['nps'] = pd.to_numeric(dfs['Dim_Nps']['nps'], errors='coerce')
            
            # Identifica valores na escala de dezenas (20, 30, 40, etc.) e normaliza para 0-10
            mask_dezenas = dfs['Dim_Nps']['nps'] > 10
            dfs['Dim_Nps'].loc[mask_dezenas, 'nps'] = dfs['Dim_Nps'].loc[mask_dezenas, 'nps'] / 10
            
            # Garante que todos os valores estão entre 0 e 10
            dfs['Dim_Nps']['nps'] = dfs['Dim_Nps']['nps'].clip(0, 10)
            
            print(f"NPS normalizado: {dfs['Dim_Nps']['nps'].min()} a {dfs['Dim_Nps']['nps'].max()}")
        
        # Pega apenas a resposta mais recente de NPS por cliente
        nps_recente = dfs['Dim_Nps'].sort_values('respondeAt').drop_duplicates('cd_cliente', keep='last')
        df = pd.merge(df, nps_recente, on='cd_cliente', how='left')
    
    # Removendo registros duplicados
    print(f"Número de registros antes da remoção de duplicados: {len(df)}")
    
    # Identifica colunas chave para remoção de duplicados
    # Aqui vamos considerar que registros são duplicados se tiverem o mesmo cliente, contrato e produto
    chaves_deduplicacao = ['cd_cliente', 'cd_contrato', 'cd_produto']
    
    # Remove duplicados mantendo o registro mais recente (se houver data) ou o primeiro
    if 'dt_consumo' in df.columns:
        df = df.sort_values('dt_consumo', ascending=False).drop_duplicates(subset=chaves_deduplicacao, keep='first')
    else:
        df = df.drop_duplicates(subset=chaves_deduplicacao, keep='first')
    
    print(f"Número de registros após remoção de duplicados: {len(df)}")
    
    # Corrigindo o uso de fillna para evitar FutureWarning em pandas 3.0
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('Não informado')
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
    
    print(f"ETL concluído. {len(df)} registros processados.")
    return df
