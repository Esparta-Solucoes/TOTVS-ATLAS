import pandas as pd
import os
from io import StringIO

# Define o caminho base para a pasta de dados, relativo à localização do script
caminho_base = os.path.join(os.path.dirname(__file__), "..", "data", "dataset_totvs")

# Define o caminho do arquivo de saída na pasta de dados
arquivo_saida = os.path.join(os.path.dirname(__file__), "..", "data", "exploracao_output_dados_brutos.txt")

# Lista dos arquivos a explorar
arquivos = [
    "clientes_desde.csv",
    "clientes_junto.csv",
    "contratacoes_ultimos_12_meses.csv",
    "dados_clientes.csv",
    "historico.csv",
    "mrr.csv",
    "nps_relacional.csv",
    "nps_transacional_aquisicao.csv",
    "nps_transacional_implantacao.csv",
    "nps_transacional_onboarding.csv",
    "nps_transacional_produto.csv",
    "nps_transacional_suporte.csv",
    "telemetria_1.csv", "telemetria_2.csv", "telemetria_3.csv", "telemetria_4.csv",
    "telemetria_5.csv", "telemetria_6.csv", "telemetria_7.csv", "telemetria_8.csv",
    "telemetria_9.csv", "telemetria_10.csv", "telemetria_11.csv",
    "tickets.csv"
]

# Função de exploração inicial aprimorada
def explorar_csv(nome_arquivo, print_func=print):
    caminho_completo = os.path.join(caminho_base, nome_arquivo)
    
    # Verifica se o arquivo existe antes de tentar ler
    if not os.path.exists(caminho_completo):
        print_func(f"AVISO: Arquivo não encontrado em '{caminho_completo}'")
        print_func("="*100 + "\n")
        return

    print_func("="*100)
    print_func(f"ARQUIVO: {nome_arquivo.upper()}")
    
    # Leitura com fallback de encoding
    try:
        df = pd.read_csv(caminho_completo, sep=";", encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(caminho_completo, sep=";", encoding="latin1")
            print_func("Aviso: arquivo lido com encoding latin1")
        except Exception as e:
            print_func(f"Erro ao ler {nome_arquivo.upper()}: {e}")
            return
    except Exception as e:
        print_func(f"Erro ao ler {nome_arquivo.upper()}: {e}")
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
    
    # Amostra aleatória limitada
    n_sample = min(5, len(df))
    print_func(f"AMOSTRA ALEATÓRIA ({n_sample} LINHAS):")
    if n_sample > 0:
        print_func(df.sample(n_sample, random_state=42).to_string())
    else:
        print_func("Não há linhas para amostrar.")
    print_func("-"*100)

    print_func("VALORES NULOS POR COLUNA:")
    print_func(df.isnull().sum().to_string())
    print_func("-"*100)
    
    print_func("DUPLICADOS:")
    print_func(df.duplicated().sum())
    print_func("-"*100)
    
    print_func("VALORES ÚNICOS POR COLUNA:")
    print_func(df.nunique().to_string())
    print_func("-"*100)

    # Estatísticas descritivas
    if len(df.select_dtypes(include='number').columns) > 0:
        print_func("ESTATÍSTICAS DESCRITIVAS (NUMÉRICAS):")
        print_func(df.describe(include='number').transpose().to_string())
    else:
        print_func("ESTATÍSTICAS DESCRITIVAS (NUMÉRICAS): Nenhuma coluna numérica encontrada.")
    print_func("-"*100)

    if len(df.select_dtypes(include='object').columns) > 0:
        print_func("ESTATÍSTICAS DESCRITIVAS (CATEGÓRICAS):")
        print_func(df.describe(include='object').transpose().to_string())
    else:
        print_func("ESTATÍSTICAS DESCRITIVAS (CATEGÓRICAS): Nenhuma coluna categórica encontrada.")
    print_func("-"*100)
    
    # Tentativa de conversão de colunas de data
    df_temp = df.copy()
    for col in df_temp.select_dtypes(include=['object']).columns:
        try:
            df_temp[col] = pd.to_datetime(df_temp[col], errors='coerce', dayfirst=True)
        except (ValueError, TypeError):
            continue
    
    date_cols = df_temp.select_dtypes(include=['datetime64[ns]']).columns
    if len(date_cols) > 0:
        print_func("ESTATÍSTICAS DESCRITIVAS (DATAS):")
        for col in date_cols:
            print_func(f"   Coluna '{col}':")
            print_func(f"     Mínimo: {df_temp[col].min()}")
            print_func(f"     Máximo: {df_temp[col].max()}")
    else:
        print_func("ESTATÍSTICAS DESCRITIVAS (DATAS): Nenhuma coluna de data encontrada ou convertida.")
    print_func("-"*100)

    print_func("="*100 + "\n")

# Função principal para executar o script
def main():
    # Abre o arquivo de log para escrita
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        # Função para imprimir no console e no arquivo
        def print_duplo(*args, **kwargs):
            # Imprime no console
            print(*args, **kwargs)
            # Imprime no arquivo de log
            print(*args, **kwargs, file=f)

        # Itera sobre a lista de arquivos e executa a exploração
        for arq in arquivos:
            explorar_csv(arq, print_func=print_duplo)

    print(f"\nAnálise concluída. Resultados salvos em: '{os.path.abspath(arquivo_saida)}'")

if __name__ == "__main__":
    main()
