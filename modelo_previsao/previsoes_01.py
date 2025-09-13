import pandas as pd
import numpy as np
import os
import urllib
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# --- FASE 0: Conexão com o Banco de Dados Azure e Carregamento dos Dados ---

def conectar_banco_azure():
    """
    Carrega as credenciais do arquivo .env e cria uma engine de conexão com o banco de dados Azure.
    """
    load_dotenv() # Carrega as variáveis de ambiente do arquivo .env

    db_server = os.getenv("DB_SERVER")
    db_database = os.getenv("DB_DATABASE")
    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")

    if not all([db_server, db_database, db_username, db_password]):
        print("ERRO: Verifique se todas as variáveis de ambiente (DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD) estão no arquivo .env")
        return None

    try:
        params = urllib.parse.quote_plus(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={db_server};"
            f"DATABASE={db_database};"
            f"UID={db_username};"
            f"PWD={db_password}"
        )
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
        print("Conexão com o banco de dados Azure bem-sucedida!")
        return engine
    except Exception as e:
        print(f"ERRO ao conectar ao banco de dados: {e}")
        return None

def carregar_dados_do_banco(engine):
    """
    Lê todas as tabelas necessárias do banco de dados para DataFrames do Pandas.
    """
    if engine is None:
        return None

    tabelas = [
        "Fato_Consumo", "Dim_Cliente", "Dim_Contrato", "Dim_Produto", "Dim_Nps",
        "Dim_Segmento", "Dim_Faturamento", "Dim_Localidade", "Dim_Modalidade",
        "Dim_StatusContrato", "Dim_Marca", "Dim_LinhaReceita"
    ]
    
    dataframes = {}
    print("\nCarregando tabelas do banco de dados...")
    try:
        with engine.connect() as conn:
            for tabela in tabelas:
                print(f"- Carregando {tabela}...")
                query = f"SELECT * FROM {tabela}"
                dataframes[tabela] = pd.read_sql(query, conn)
        print("Todas as tabelas foram carregadas com sucesso.")
        return dataframes
    except Exception as e:
        print(f"ERRO ao carregar tabelas: {e}")
        return None

# Conectar e carregar os dados
engine = conectar_banco_azure()
dfs = carregar_dados_do_banco(engine)

if dfs is None:
    print("Processo interrompido devido a erro no carregamento dos dados.")
    exit()

# --- FASE 1: Consolidação e Preparação dos Dados (Lógica Aprimorada) ---

print("\nFASE 1: Consolidando e preparando os dados...")

# Juntar Fato_Consumo com informações do contrato para enriquecer os dados antes de agregar
consumo_enriquecido = pd.merge(dfs['Fato_Consumo'], dfs['Dim_Contrato'], on='cd_contrato', how='left')
consumo_enriquecido = pd.merge(consumo_enriquecido, dfs['Dim_StatusContrato'], on='cd_status', how='left')
consumo_enriquecido = pd.merge(consumo_enriquecido, dfs['Dim_Modalidade'], on='cd_modalidade', how='left')

# Agregar dados de consumo por cliente
consumo_agregado = consumo_enriquecido.groupby('cd_cliente').agg(
    vl_total_gasto=('vl_total', 'sum'),
    vl_medio_gasto=('vl_total', 'mean'),
    vl_total_desconto=('vl_desconto', 'sum'),
    qtd_compras=('cd_produto', 'count'),
    situacao_contrato=('situacao_contrato', lambda x: x.mode()[0] if not x.mode().empty else 'N/A'),
    modal_comerc=('modal_comerc', lambda x: x.mode()[0] if not x.mode().empty else 'N/A')
).reset_index()

# Para a tabela de NPS, vamos pegar a resposta mais recente de cada cliente
dfs['Dim_Nps']['respondeAt'] = pd.to_datetime(dfs['Dim_Nps']['respondeAt'])
nps_recente = dfs['Dim_Nps'].sort_values('respondeAt').drop_duplicates('cd_cliente', keep='last')

# A base agora são os clientes que efetivamente tiveram consumo.
df = pd.merge(consumo_agregado, dfs['Dim_Cliente'], on='cd_cliente', how='inner')

# Agora, enriquecemos essa base com os dados de NPS e as descrições
df = pd.merge(df, nps_recente, on='cd_cliente', how='left')
df = pd.merge(df, dfs['Dim_Segmento'], on='cd_segmento', how='left')
df = pd.merge(df, dfs['Dim_Faturamento'], on='cd_faturamento', how='left')

# Lidar com dados faltantes (estratégia aprimorada para evitar warnings)
for col in df.columns:
    if pd.api.types.is_object_dtype(df[col]):
        df[col] = df[col].fillna('N/A')
    elif pd.api.types.is_datetime64_any_dtype(df[col]):
        df[col] = df[col].fillna(pd.Timestamp('1970-01-01'))
    else:
        df[col] = df[col].fillna(0)

# --- FASE 2: Segmentação de Clientes (K-Means) ---
# CORREÇÃO: Aplicar a clusterização no DataFrame 'df' completo antes de filtrar para modelagem.
print("FASE 2: Segmentando clientes com K-Means...")

features_cluster = ['vl_total_gasto', 'qtd_compras', 'cd_faturamento']
X_cluster = df[features_cluster]

scaler = StandardScaler()
X_cluster_scaled = scaler.fit_transform(X_cluster)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
# Adiciona a coluna 'segmento_cliente' ao DataFrame principal 'df'
df['segmento_cliente'] = kmeans.fit_predict(X_cluster_scaled)

print("Análise dos Segmentos de Clientes (Médias por cluster):")
print(df.groupby('segmento_cliente')[features_cluster].mean())
print("\n" + "="*50 + "\n")

# --- FASE 1.5: Preparação final para modelagem ---
# Agora, filtramos o DataFrame 'df' (que já tem o segmento) para criar a base de modelagem.
def classificar_nps(nota):
    if nota <= 6:
        return 'Detrator'
    elif nota <= 8:
        return 'Neutro'
    else: # nota > 8
        return 'Promotor'

df_com_nps = df[df['resposta_NPS'] != 0].copy()
df_com_nps['categoria_nps'] = df_com_nps['resposta_NPS'].apply(classificar_nps)
df_modelagem = df_com_nps.copy()

print("DataFrame consolidado e preparado para modelagem:")
print(df_modelagem[['cd_cliente', 'ds_segmento', 'vl_total_gasto', 'categoria_nps', 'segmento_cliente']].head())
print(f"Total de clientes com consumo e NPS para modelagem: {len(df_modelagem)}")
print("\n" + "="*50 + "\n")


# --- FASE 3: Modelo Preditivo de NPS ---

print("FASE 3: Treinando modelo para prever a categoria NPS...")

features_modelo = [
    'vl_total_gasto', 'qtd_compras', 'vl_total_desconto', 
    'ds_segmento', 'faixa_faturamento', 'segmento_cliente',
    'situacao_contrato', 'modal_comerc'
]
target_modelo = 'categoria_nps'

X = df_modelagem[features_modelo]
y = df_modelagem[target_modelo]

categorical_features = ['ds_segmento', 'faixa_faturamento', 'situacao_contrato', 'modal_comerc']
numerical_features = ['vl_total_gasto', 'qtd_compras', 'vl_total_desconto']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ],
    remainder='passthrough'
)

# MELHORIA: Adicionar 'class_weight' para lidar com o desbalanceamento de classes
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(random_state=42, n_estimators=100, class_weight='balanced'))
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Relatório de Classificação do Modelo Preditivo:")
print(classification_report(y_test, y_pred))
print("\n" + "="*50 + "\n")

print("FASE 3.1: Análise dos fatores mais influentes no NPS...")
feature_names_raw = model.named_steps['preprocessor'].get_feature_names_out()
feature_names = [name.split('__')[-1] for name in feature_names_raw]
importances = model.named_steps['classifier'].feature_importances_
feature_importance_df = pd.DataFrame({'feature': feature_names, 'importance': importances})
feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
print("Principais Variáveis que Influenciam o NPS:")
print(feature_importance_df.head(10))
print("\n" + "="*50 + "\n")


# --- FASE 4: Geração da Tabela de Previsão ---

print("FASE 4: Gerando a tabela final de previsão...")

# CORREÇÃO: Agora 'df' já tem a coluna 'segmento_cliente' e a predição funcionará.
df['nps_previsto_categoria'] = model.predict(df[features_modelo])

mapa_nota = {'Promotor': 9, 'Neutro': 8, 'Detrator': 5}
df['resposta_NPS_previsao'] = df['nps_previsto_categoria'].map(mapa_nota)

tabela_previsao = df[[
    'cd_cliente', 'vl_total_gasto', 'vl_total_desconto', 'qtd_compras',
    'faixa_faturamento', 'ds_segmento', 'modal_comerc', 'situacao_contrato',
    'resposta_NPS', 'resposta_NPS_previsao'
]].copy()

tabela_previsao.rename(columns={
    'vl_total_gasto': 'vl_total_historico', 
    'vl_total_desconto': 'vl_desconto_historico',
    'qtd_compras': 'qtd_produtos_historico', 
    'faixa_faturamento': 'fat_faixa',
    'resposta_NPS': 'nps_historico_nota'
}, inplace=True)

tabela_previsao['mes_previsao'] = (pd.to_datetime('today') + pd.DateOffset(months=1)).strftime('%Y-%m')
tabela_previsao['vl_total_previsao'] = tabela_previsao['vl_total_historico'] * 1.05 # Simulação simples
tabela_previsao['vl_desconto_previsao'] = tabela_previsao['vl_desconto_historico'] * 1.02 # Simulação simples
tabela_previsao['situacao_contrato_previsao'] = np.where(tabela_previsao['situacao_contrato'] == 'ATIVO', 'Manter Ativo', 'Risco de Churn')

print("Amostra da Tabela de Previsão para o Dashboard:")
print(tabela_previsao.head())

tabela_previsao.to_csv('dados_previsao_output.csv', index=False)
print("\nArquivo 'dados_previsao_output.csv' gerado com sucesso!")