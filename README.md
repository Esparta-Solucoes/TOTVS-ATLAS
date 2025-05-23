<h1 align="center">TOTVS ATLAS</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" />
  <img src="https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white" />
  <img src="https://img.shields.io/badge/cuda-000000.svg?style=for-the-badge&logo=nVIDIA&logoColor=green" />
</p>

## Sobre o Projeto

O **TOTVS Atlas** é um projeto desenvolvido para responder aos desafios apresentados no **Enterprise Challenge 2025** da FIAP. A proposta consiste na criação de um agente de inteligência artificial (IA) capaz de interpretar relatórios complexos, gerar insights relevantes e sugerir ações personalizadas aos stakeholders de cada empresa.

## Objetivo

Criar um agente de IA orquestrado, integrando técnicas avançadas de:

* **Clusterização inteligente de clientes**
* **Análise preditiva**
* **Geração de relatórios automatizados**

O objetivo central é personalizar a jornada dos clientes da TOTVS, atuando como um **"copiloto analítico"** que interpreta dados em tempo real, gera insights estratégicos e recomenda ações específicas para retenção, aumento da satisfação e exploração de oportunidades de negócio.

## Público-Alvo

* **Interno (TOTVS)**:

  * Gestores e analistas das áreas de:

    * Sucesso do Cliente
    * Suporte
    * Marketing
    * Comercial

* **Externo (Clientes Empresariais B2B)**:

  * Empresas de diversos setores:

    * Saúde
    * Varejo
    * Logística
    * Outros segmentos relevantes

## Impacto Esperado

* ✅ **Aumento da satisfação dos clientes TOTVS** por meio da personalização da jornada do cliente.
* 📈 **Redução significativa do churn**, através da detecção proativa de riscos.
* 🚀 **Aumento da receita** com estratégias inteligentes de upsell e cross-sell orientadas por dados.
* ⚡ **Maior agilidade na tomada de decisão**, impulsionada por suporte contínuo da IA.

## Diferenciais Competitivos

| Característica                   | Soluções Tradicionais | TOTVS Atlas                              |
| -------------------------------- | --------------------- | ---------------------------------------- |
| **Segmentação de clientes**      | Genérica ou manual    | Clusterização inteligente com IA         |
| **Insights e recomendações**     | Relatórios estáticos  | Insights dinâmicos orientados por dados  |
| **Estratégia de personalização** | Genérica              | Adaptada ao perfil específico do cliente |
| **Compreensão de linguagem**     | Não disponível        | Consultas utilizando modelos de LLM      |
| **Integração de dados**          | Fragmentada           | Pipeline unificado e orquestrado         |

## Tecnologias Utilizadas

* Inteligência Artificial (IA)
* RAG
* Machine Learning (ML)
* BI
* Vectorstore
* SGBD
* Cloud
* Clusterização

## ⚙️ Como executar:

### Pré-requisitos

1. Instale o **Poetry** (gerenciador de pacotes) na versão **2.1.1**:

**Windows:**

```bash
(Invoke-WebRequest -Uri https://install.python-poetry.org/2.1.1 -UseBasicParsing).Content | py -
```

**Mac/Linux:**

```bash
curl -sSL https://install.python-poetry.org/2.1.1 | python3 -
```

**Verifique a instalação:**

```bash
poetry --version  # Deve exibir: Poetry (version 2.1.1)
```

Se você tiver uma versão diferente instalada, pode desinstalá-la primeiro:

```bash
# Windows
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py - --uninstall

# Mac/Linux
curl -sSL https://install.python-poetry.org | python3 - --uninstall
```

### Instalando dependências e configurando o ambiente

```bash
# Instale as dependências usando o Poetry
poetry install

# Ative o ambiente do Poetry
poetry shell
```

### ⚠️ Atenção

A partir da versão **2.4**, o **PyTorch** oferece suporte oficial ao **Python 3.12**, incluindo a funcionalidade `torch.compile`. Para garantir máxima estabilidade e compatibilidade com todas as bibliotecas utilizadas neste projeto, recomendamos o uso do **Python 3.11.8**, conforme especificado no arquivo `pyproject.toml`.

## Equipe

- [Esparta-Soluções](https://github.com/Esparta-Solucoes)

---

© 2025 - Projeto desenvolvido para o Enterprise Challenge 2025 da FIAP
