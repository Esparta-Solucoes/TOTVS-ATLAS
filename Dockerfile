# ==============================================================================
#  Dockerfile para TOTVS ATLAS
#  Utiliza multi-stage builds para otimizar as imagens de desenvolvimento e produção.
# ==============================================================================

# ==================
# 1) Base Stage: Define a imagem Python base e variáveis de ambiente comuns.
# ==================
FROM python:3.11-slim AS base

# Garante que o output do Python seja enviado diretamente para o terminal,
# previne a criação de arquivos .pyc e define um hash seed aleatório.
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

# ==================
# 2) Builder Stage: Instala dependências do sistema, Poetry e as dependências do projeto.
# ==================
FROM base AS builder

# Configurações do Poetry para um ambiente não-interativo e otimizado para CI/CD.
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION='1.8.2' 

# Instala dependências do sistema necessárias para compilar pacotes e para o driver ODBC.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instala o driver ODBC para SQL Server (método moderno sem apt-key).
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instala o Poetry na versão especificada.
RUN curl -sSL https://install.python-poetry.org | python3 -

# Define o diretório de trabalho.
WORKDIR /app

# Copia os arquivos de definição de dependências.
COPY pyproject.toml poetry.lock ./

# Instala apenas as dependências de produção.
# Isso cria um ambiente "limpo" que será copiado para a imagem de produção final.
RUN poetry install --no-root --only main

# ==================
# 3) Production Stage: Cria a imagem final, leve, para produção.
# ==================
FROM base AS production

# Define o diretório de trabalho.
WORKDIR /app

# Instala apenas as dependências de tempo de execução (runtime) essenciais.
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia o ambiente virtual com as dependências instaladas do estágio 'builder'.
COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia apenas o código da aplicação necessário para rodar.
COPY ./APP ./APP
COPY ./main.py .

# Cria um usuário não-root para executar a aplicação (boa prática de segurança).
RUN useradd -m -u 1000 appuser
USER appuser

# Expõe a porta que a aplicação vai usar.
EXPOSE 8000

# Comando para iniciar a aplicação em produção com Gunicorn.
# Gunicorn gerencia os workers Uvicorn, tornando o servidor mais robusto.
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]