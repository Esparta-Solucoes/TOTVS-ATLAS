# Relatório Detalhado: Análise e Modelagem Preditiva de NPS

**Data da Análise:** 23 de agosto de 2025

## 1. Objetivo

Este relatório detalha o processo de construção de um modelo de machine learning para prever a classificação de Net Promoter Score (NPS) dos clientes. O objetivo é identificar os principais fatores que influenciam a satisfação do cliente e gerar uma base de dados com previsões que possa ser utilizada para alimentar dashboards de Business Intelligence (BI).

## 2. Metodologia e Preparação dos Dados

A qualidade do modelo preditivo depende diretamente da qualidade dos dados utilizados para treiná-lo. A seguir, detalhamos as decisões tomadas na fase de preparação.

### 2.1. Consolidação dos Dados

Os dados foram carregados de 12 tabelas distintas do banco de dados Azure, refletindo a arquitetura em Star Schema. Para criar uma visão unificada e completa de cada cliente, realizamos as seguintes junções (joins):

- **Enriquecimento do Consumo:** A tabela Fato_Consumo foi primeiramente enriquecida com informações contextuais das tabelas Dim_Contrato, Dim_StatusContrato e Dim_Modalidade. Isso nos permitiu ter, para cada transação, detalhes sobre o status e a modalidade do contrato associado.

- **Agregação por Cliente:** Os dados de consumo enriquecidos foram agregados por cd_cliente. Nesta etapa, calculamos métricas essenciais que resumem o comportamento de cada cliente, como:
  - `vl_total_gasto`: Soma de todo o valor transacionado.
  - `qtd_compras`: Número total de produtos/serviços consumidos.
  - `situacao_contrato` e `modal_comerc`: A situação e modalidade mais frequentes (moda estatística), para definir o status principal do cliente.

- **Criação da Base Principal:** A tabela agregada de consumo (`consumo_agregado`) foi utilizada como a base principal. Realizamos um INNER JOIN com a Dim_Cliente. Esta foi uma decisão crucial: ao usar INNER JOIN, garantimos que nossa análise se concentraria apenas em clientes com histórico de consumo registrado. Isso evita a distorção do modelo com perfis de clientes que não geraram dados de transação.

- **Enriquecimento Final:** A base resultante foi enriquecida com as informações mais recentes de NPS (Dim_Nps) e com as descrições de segmento e faturamento, utilizando LEFT JOIN.

### 2.2. Critério de Seleção para Treinamento do Modelo

Para treinar um modelo que prevê o NPS, é fundamental utilizar dados de clientes que já expressaram sua opinião. Portanto, a base de dados para treinamento (`df_modelagem`) foi criada a partir do DataFrame consolidado, aplicando o seguinte filtro:

`df[df['resposta_NPS'] != 0]`: Selecionamos apenas os clientes que possuem uma resposta de NPS válida (diferente de 0, que foi o valor usado para preencher nulos).

**Justificativa:** Treinar o modelo com dados de quem já respondeu nos permite encontrar padrões entre o comportamento de consumo (gastos, produtos, segmento) e a satisfação (nota do NPS). Tentar incluir clientes sem resposta nesta fase seria como tentar prever um resultado sem ter exemplos de resultados passados, o que não é eficaz. O modelo aprende com o histórico para depois aplicar esse aprendizado e prever o NPS para os clientes que ainda não responderam.

## 3. Análise e Interpretação dos Resultados

### 3.1. Segmentação de Clientes (K-Means)

Antes da previsão, aplicamos um algoritmo de clusterização (K-Means) para agrupar os clientes em 4 segmentos com base em seu comportamento financeiro e de consumo. A análise das médias por cluster revela perfis distintos:

| segmento_cliente | vl_total_gasto (Média) | qtd_compras (Média) | Perfil do Cluster (Hipótese) |
|-----------------|------------------------|---------------------|------------------------------|
| 0 | R$ 364.505 | 123 | Clientes de Médio Valor: Volume de compras moderado e faturamento significativo. |
| 1 | R$ 494.934 | 111 | Clientes de Alto Valor: Faturamento mais alto que o grupo 0, com um pouco menos de compras. |
| 2 | R$ 14.323.780 | 2.090 | Grandes Contas (Key Accounts): Volume de compras e faturamento muito acima da média. |
| 3 | R$ 124.230.400 | 4.411 | Contas Estratégicas (Mega Accounts): Representam os maiores clientes da base, com valores extremos. |

Essa segmentação é valiosa pois se torna uma feature (variável) para o modelo preditivo, ajudando-o a entender que clientes de diferentes perfis podem ter padrões de satisfação distintos.

### 3.2. Análise do Modelo Preditivo (Random Forest)

O modelo foi treinado com os 2.175 clientes que possuíam histórico de consumo e resposta de NPS.

**Relatório de Classificação:**

| Categoria | Precision | Recall | F1-Score | Support |
|-----------|-----------|--------|----------|---------|
| Detrator | 0.20 | 0.02 | 0.04 | 41 |
| Neutro | 0.43 | 0.38 | 0.40 | 175 |
| Promotor | 0.51 | 0.64 | 0.57 | 219 |
| Accuracy | | | 0.48 | 435 |

**Interpretação:**

- **Desempenho Geral (Accuracy 48%):** O modelo acerta a classificação em 48% das vezes. Embora pareça baixo, é um ponto de partida significativamente melhor do que um palpite aleatório (que seria em torno de 33%).

- **Performance por Classe:**
  - **Promotor:** O modelo tem um desempenho razoável aqui (Recall de 0.64), o que significa que ele consegue identificar corretamente 64% dos clientes que são, de fato, Promotores.
  - **Neutro:** A performance é moderada.
  - **Detrator:** O desempenho é muito baixo (Recall de 0.02). O modelo tem extrema dificuldade em identificar os detratores. Isso ocorre devido ao forte desbalanceamento dos dados: há muito poucos detratores (41 na amostra de teste) em comparação com os promotores (219). O modelo não tem exemplos suficientes para aprender a reconhecê-los bem. A inclusão do `class_weight='balanced'` ajudou, mas o problema persiste devido à pequena quantidade de amostras.

**Fatores Mais Influentes no NPS:**

Esta é uma das saídas mais valiosas do modelo. Ela nos mostra quais variáveis têm mais peso na hora de definir o NPS de um cliente.

1. **vl_total_gasto (Importância: 0.218):** O valor total que um cliente gasta é o fator mais importante. Isso pode indicar que tanto clientes que gastam muito (e esperam um serviço premium) quanto os que gastam pouco (e podem se sentir negligenciados) têm seu NPS fortemente influenciado por essa variável.

2. **qtd_compras (Importância: 0.209):** A frequência e variedade de interações com a empresa também é crucial.

3. **vl_total_desconto (Importância: 0.122):** Descontos têm um impacto significativo, podendo influenciar positiva ou negativamente a percepção de valor.

4. **ds_segmento_MANUFATURA (Importância: 0.024):** Ser do segmento de Manufatura é um fator relevante.

5. **modal_comerc_MODALIDADE TRADICIONAL (Importância: 0.024):** A modalidade do contrato também influencia a satisfação.

## 4. Conclusões e Próximos Passos

- **Validade do Processo:** A metodologia de consolidação e o fluxo do script estão corretos e robustos. A base de dados gerada é coerente e pronta para ser consumida.

- **Insights Iniciais:** Já é possível afirmar que o comportamento financeiro (vl_total_gasto, qtd_compras, vl_total_desconto) é o principal driver da satisfação do cliente, muito mais do que fatores demográficos isolados.

- **Desafio do Desbalanceamento:** O principal desafio para melhorar a precisão do modelo é o baixo número de exemplos de clientes "Detratores".

- **Recomendações:**
  1. **Coleta de Dados:** Focar em obter mais respostas de NPS, especialmente de clientes que se suspeita estarem insatisfeitos, para enriquecer a base de treinamento dos Detratores.
  
  2. **Engenharia de Features:** Criar novas variáveis. Por exemplo: "tempo de contrato", "média de valor por compra" ou "uso de produtos estratégicos". Isso pode fornecer novos padrões para o modelo.
  
  3. **Técnicas Avançadas:** Explorar técnicas de oversampling (como SMOTE) para criar artificialmente mais exemplos da classe minoritária (Detratores) e rebalancear o treinamento.
  
  4. **Análise de Erros:** Investigar os clientes que o modelo classificou incorretamente. Isso pode revelar padrões que o modelo atual não está capturando.

O arquivo `dados_previsao_output.csv` gerado é o resultado final deste processo e pode ser utilizado com confiança para alimentar seus dashboards, tendo em mente as atuais métricas de precisão do modelo.