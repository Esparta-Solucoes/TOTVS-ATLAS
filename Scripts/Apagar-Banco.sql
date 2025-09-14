USE TOTVS_DW;
GO

-- Desativar verificação de chaves estrangeiras temporariamente
EXEC sp_msforeachtable "ALTER TABLE ? NOCHECK CONSTRAINT ALL";
GO

-- Dropar tabela fato primeiro
IF OBJECT_ID('Fato_Consumo', 'U') IS NOT NULL
    DROP TABLE Fato_Consumo;
GO

-- Dropar tabelas dependentes de outras dimensões
IF OBJECT_ID('Dim_Cliente', 'U') IS NOT NULL
    DROP TABLE Dim_Cliente;
GO

IF OBJECT_ID('Dim_Produto', 'U') IS NOT NULL
    DROP TABLE Dim_Produto;
GO

IF OBJECT_ID('Dim_Contrato', 'U') IS NOT NULL
    DROP TABLE Dim_Contrato;
GO

-- Dropar tabelas independentes
IF OBJECT_ID('Dim_Segmento', 'U') IS NOT NULL
    DROP TABLE Dim_Segmento;
GO

IF OBJECT_ID('Dim_Faturamento', 'U') IS NOT NULL
    DROP TABLE Dim_Faturamento;
GO

IF OBJECT_ID('Dim_Localidade', 'U') IS NOT NULL
    DROP TABLE Dim_Localidade;
GO

IF OBJECT_ID('Dim_Marca', 'U') IS NOT NULL
    DROP TABLE Dim_Marca;
GO

IF OBJECT_ID('Dim_LinhaReceita', 'U') IS NOT NULL
    DROP TABLE Dim_LinhaReceita;
GO

IF OBJECT_ID('Dim_Modalidade', 'U') IS NOT NULL
    DROP TABLE Dim_Modalidade;
GO

IF OBJECT_ID('Dim_StatusContrato', 'U') IS NOT NULL
    DROP TABLE Dim_StatusContrato;
GO

IF OBJECT_ID('Dim_Tempo', 'U') IS NOT NULL
    DROP TABLE Dim_Tempo;
GO

-- Reativar constraints
EXEC sp_msforeachtable "ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL";
GO
