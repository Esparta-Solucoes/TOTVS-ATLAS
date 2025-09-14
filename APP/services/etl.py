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
        "Dim_StatusContrato", "Dim_Marca", "Dim_LinhaReceita", "Dim_Tempo",
        "Tb_Previsao"  # Nova tabela adicionada
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
    
    # Adicionar a nova tabela de previsão ao dataframe consolidado
    if 'Tb_Previsao' in dfs and 'cd_cliente' in dfs['Tb_Previsao'].columns:
        print("Integrando dados da tabela Tb_Previsao...")
        # Remover duplicatas de cd_cliente para garantir join 1:1
        previsao_df = dfs['Tb_Previsao'].drop_duplicates(subset=['cd_cliente'], keep='first')
        # Selecionar apenas as colunas de interesse para o join
        colunas_previsao = [
            'cd_cliente', 'vl_total_historico', 'vl_desconto_historico', 
            'qtd_produtos_historico', 'fat_faixa', 'resposta_NPS_previsao', 
            'mes_previsao', 'vl_total_previsao', 'vl_desconto_previsao', 
            'situacao_contrato_previsao'
        ]
        # Filtrar apenas as colunas que existem no DataFrame
        colunas_existentes = [col for col in colunas_previsao if col in previsao_df.columns]
        if len(colunas_existentes) < len(colunas_previsao):
            print(f"Aviso: Algumas colunas esperadas não foram encontradas na tabela Tb_Previsao.")
            print(f"Colunas esperadas: {colunas_previsao}")
            print(f"Colunas encontradas: {previsao_df.columns.tolist()}")
        
        # Realizar o join com as colunas existentes
        df = pd.merge(df, previsao_df[colunas_existentes], on='cd_cliente', how='left')
        print(f"Dados de previsão integrados. Adicionadas {len(colunas_existentes)} colunas.")
    else:
        print("Aviso: Tabela Tb_Previsao não encontrada ou não contém a coluna cd_cliente.")
    
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
