# Análise Exploratória e Datasets

Este diretório contém os conjuntos de dados utilizados no projeto e os resultados da análise exploratória de dados (EDA).

## Arquivos de Saída da Análise (EDA)

- `exploracao_output_dados_brutos.txt`: Este arquivo contém uma análise detalhada dos arquivos CSV brutos fornecidos pela TOTVS. Para cada arquivo, o script `exploracao_inicial_dados_brutos_totvs.py` (localizado em `APP/notebooks/`) gera as seguintes informações:
  - Dimensões do DataFrame (linhas e colunas)
  - Informações gerais (tipos de dados, contagem de nulos)
  - Nomes das colunas
  - Amostra das primeiras e últimas linhas
  - Contagem de valores nulos e vazios
  - Número de linhas duplicadas
  - Contagem de valores únicos por coluna
  - Estatísticas descritivas para colunas numéricas e categóricas
  - Análise de colunas de data

- `exploracao_output_dados_tratados.txt`: Este arquivo contém a análise exploratória das tabelas do banco de dados SQL, após o processo de ETL. O script `exploracao_inicial_dados_tratados_totvs.py` (localizado em `APP/notebooks/`) se conecta ao banco de dados e analisa cada tabela do modelo dimensional (Fato e Dimensões), gerando as mesmas métricas descritas para os dados brutos.

## Datasets

Este diretório contém os conjuntos de dados utilizados no projeto.

## `dataset_exemplo`

Este diretório contém um conjunto de dados de exemplo que pode ser utilizado para testes e desenvolvimento inicial.

## `dataset_totvs`

Este diretório contém o conjunto de dados principal fornecido pela TOTVS para o desafio.

O download do dataset pode ser feito através do seguinte link: [Link para o dataset](https://fiapcom-my.sharepoint.com/:u:/g/personal/rm557895_fiap_com_br/EezxPdrpteVJlyo3GXJjlksBo4_my9RVjX6NJHCaoXdPPQ?e=sMXPdr)