PRAGMA foreign_keys = ON;

-- =========================
-- Marcas
-- =========================

DROP TABLE IF EXISTS marcas;

CREATE TABLE IF NOT EXISTS marcas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

-- =========================
-- Modelos
-- =========================

DROP TABLE IF EXISTS modelos;

CREATE TABLE IF NOT EXISTS modelos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marca_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    url TEXT NOT NULL,

    FOREIGN KEY (marca_id) REFERENCES marcas(id),
    UNIQUE (marca_id, nome)
);

-- =========================
-- Modelos x Anos
-- =========================

DROP TABLE IF EXISTS modelos_anos;

CREATE TABLE IF NOT EXISTS modelos_anos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_id INTEGER NOT NULL,
    ano INTEGER NOT NULL,

    FOREIGN KEY (modelo_id) REFERENCES modelos(id),
    UNIQUE (modelo_id, ano)
);

-- =========================
-- Versões
-- =========================

DROP TABLE IF EXISTS versoes;

CREATE TABLE IF NOT EXISTS versoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modelo_ano_id INTEGER NOT NULL,
    versao TEXT NOT NULL,
    url TEXT NOT NULL,

    FOREIGN KEY (modelo_ano_id) REFERENCES modelos_anos(id),
    UNIQUE (modelo_ano_id, versao)
);

-- =========================
-- Detalhes das versões
-- =========================

DROP TABLE IF EXISTS versoes_detalhes;

CREATE TABLE IF NOT EXISTS versoes_detalhes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    versao_id INTEGER UNIQUE NOT NULL,

    -- Combustível e tanque
    combustivel TEXT,
    tanque_litros REAL,

    -- Consumo
    consumo_cidade_alcool REAL,
    consumo_cidade_gasolina REAL,
    consumo_estrada_alcool REAL,
    consumo_estrada_gasolina REAL,

    -- Motor e desempenho
    cilindrada_cm3 INTEGER,
    cilindros TEXT,
    velocidade_max_kmh INTEGER,
    zero_a_cem_segundos REAL,

    -- Dimensões e capacidades
    comprimento_mm INTEGER,
    largura_mm INTEGER,
    altura_mm INTEGER,
    entre_eixos_mm INTEGER,
    peso_kg INTEGER,
    porta_malas_litros INTEGER,

    -- Transmissão e suspensão
    cambio TEXT,
    tracao TEXT,
    suspensao_dianteira TEXT,
    suspensao_traseira TEXT,
    freio_dianteiro TEXT,
    freio_traseiro TEXT,

    FOREIGN KEY (versao_id) REFERENCES versoes(id)
);
