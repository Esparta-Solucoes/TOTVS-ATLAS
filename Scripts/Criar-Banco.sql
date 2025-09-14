-- Criar Banco de Dados
CREATE DATABASE TOTVS_DW;
GO
USE TOTVS_DW;
GO

/* ============================
   DIMENSÕES
   ============================ */

-- Dimensão Segmento
CREATE TABLE Dim_Segmento (
    cd_segmento INT IDENTITY PRIMARY KEY,
    ds_segmento NVARCHAR(100),
    ds_subsegmento NVARCHAR(100)
);

-- Dimensão Faturamento
CREATE TABLE Dim_Faturamento (
    cd_faturamento INT IDENTITY PRIMARY KEY,
    faixa_faturamento NVARCHAR(50)
);

-- Dimensão Localidade
CREATE TABLE Dim_Localidade (
    cd_localidade INT IDENTITY PRIMARY KEY,
    uf CHAR(2),
    pais NVARCHAR(50)
);

-- Dimensão Cliente
CREATE TABLE Dim_Cliente (
    cd_cliente NVARCHAR(50) PRIMARY KEY,
    cd_segmento INT,
    cd_faturamento INT,
    cd_localidade INT,
    FOREIGN KEY (cd_segmento) REFERENCES Dim_Segmento(cd_segmento),
    FOREIGN KEY (cd_faturamento) REFERENCES Dim_Faturamento(cd_faturamento),
    FOREIGN KEY (cd_localidade) REFERENCES Dim_Localidade(cd_localidade)
);

-- Dimensão Marca
CREATE TABLE Dim_Marca (
    cd_marca INT IDENTITY PRIMARY KEY,
    marca_totvs NVARCHAR(100)
);

-- Dimensão Linha de Receita
CREATE TABLE Dim_LinhaReceita (
    cd_lin_rec INT IDENTITY PRIMARY KEY,
    ds_lin_rec NVARCHAR(100)
);

-- Dimensão Produto
CREATE TABLE Dim_Produto (
    cd_produto INT IDENTITY PRIMARY KEY,
    ds_produto NVARCHAR(200),
    cd_marca INT,
    cd_lin_rec INT,
    FOREIGN KEY (cd_marca) REFERENCES Dim_Marca(cd_marca),
    FOREIGN KEY (cd_lin_rec) REFERENCES Dim_LinhaReceita(cd_lin_rec)
);

-- Dimensão Modalidade Comercial
CREATE TABLE Dim_Modalidade (
    cd_modalidade INT IDENTITY PRIMARY KEY,
    modal_comerc NVARCHAR(100)
);

-- Dimensão Status Contrato
CREATE TABLE Dim_StatusContrato (
    cd_status INT IDENTITY PRIMARY KEY,
    situacao_contrato NVARCHAR(100)
);

-- Dimensão Contrato
CREATE TABLE Dim_Contrato (
    cd_contrato INT IDENTITY PRIMARY KEY,
    dt_assinatura_contrato DATE,
    cd_modalidade INT,
    cd_status INT,
    FOREIGN KEY (cd_modalidade) REFERENCES Dim_Modalidade(cd_modalidade),
    FOREIGN KEY (cd_status) REFERENCES Dim_StatusContrato(cd_status)
);

-- Dimensão Tempo
CREATE TABLE Dim_Tempo (
    cd_tempo INT IDENTITY PRIMARY KEY,
    dia INT,
    ano INT,
    mes INT,
    trimestre INT,
    semana INT
);

-- Dimensão NPS
CREATE TABLE Dim_Nps (
    cd_nps INT IDENTITY(1,1) PRIMARY KEY,
    cd_cliente NVARCHAR(50),
    respondeAt DATE,
    resposta_NPS INT,
    resposta_unidade INT,
    nota_SupTec_Agilidade INT,
    nota_SupTec_Atendimento INT,
    nota_Comercial INT,
    nota_Custos INT,
    nota_AdmFin_Atendimento INT,
    nota_Sofware INT,
    nota_Software_Atualizacao INT

    FOREIGN KEY (cd_cliente) REFERENCES Dim_Cliente(cd_cliente),
);

 /* ============================
    TABELA FATO
    ============================ */

CREATE TABLE Fato_Consumo (
    id_fato BIGINT IDENTITY PRIMARY KEY,
    cd_cliente NVARCHAR(50),
    cd_produto INT,
    cd_contrato INT,
    cd_tempo INT,
    qtd_produtos_contratados INT,
    meses_bonif INT,
    prc_unitario DECIMAL(22, 14),
    vl_pct_desc_temp DECIMAL(22, 14),
    vl_pct_desconto DECIMAL(22, 14),
    vl_desconto_temporario DECIMAL(22, 14),
    vl_desconto DECIMAL(22, 14),
    vl_total DECIMAL(22, 14),
    vl_full DECIMAL (22, 14)

    FOREIGN KEY (cd_cliente) REFERENCES Dim_Cliente(cd_cliente),
    FOREIGN KEY (cd_produto) REFERENCES Dim_Produto(cd_produto),
    FOREIGN KEY (cd_contrato) REFERENCES Dim_Contrato(cd_contrato),
    FOREIGN KEY (cd_tempo) REFERENCES Dim_Tempo(cd_tempo)
);
