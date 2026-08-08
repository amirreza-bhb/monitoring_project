USE ecoMonitoringDB;
GO

/* ============================================================
   1. dbo - Market Data Tables
   ============================================================ */

CREATE TABLE dbo.brent_oil_prices (
    id INT IDENTITY(1,1) NOT NULL,
    date_g DATE NOT NULL,
    date_j VARCHAR(10) NOT NULL,
    open_value DECIMAL(18,0) NULL,
    low_value DECIMAL(18,0) NULL,
    high_value DECIMAL(18,0) NULL,
    close_value DECIMAL(18,0) NULL,

    CONSTRAINT PK_brent_oil_prices
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_brent_oil_prices_date_g
        UNIQUE (date_g)
);
GO


CREATE TABLE dbo.gold_prices_18k (
    id INT IDENTITY(1,1) NOT NULL,
    date_g DATE NOT NULL,
    date_j VARCHAR(10) NOT NULL,
    open_value DECIMAL(18,0) NULL,
    low_value DECIMAL(18,0) NULL,
    high_value DECIMAL(18,0) NULL,
    close_value DECIMAL(18,0) NULL,

    CONSTRAINT PK_gold_prices_18k
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_gold_prices_18k_date_g
        UNIQUE (date_g)
);
GO


CREATE TABLE dbo.gold_prices_global (
    id INT IDENTITY(1,1) NOT NULL,
    date_g DATE NOT NULL,
    date_j VARCHAR(10) NOT NULL,
    open_value DECIMAL(18,0) NULL,
    low_value DECIMAL(18,0) NULL,
    high_value DECIMAL(18,0) NULL,
    close_value DECIMAL(18,0) NULL,

    CONSTRAINT PK_gold_prices_global
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_gold_prices_global_date_g
        UNIQUE (date_g)
);
GO


CREATE TABLE dbo.usd_free_market_rates (
    id INT IDENTITY(1,1) NOT NULL,
    date_g DATE NOT NULL,
    date_j VARCHAR(10) NOT NULL,
    open_value DECIMAL(18,0) NULL,
    low_value DECIMAL(18,0) NULL,
    high_value DECIMAL(18,0) NULL,
    close_value DECIMAL(18,0) NULL,

    CONSTRAINT PK_usd_free_market_rates
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_usd_free_market_rates_date_g
        UNIQUE (date_g)
);
GO


CREATE TABLE dbo.usd_official_rates (
    id INT IDENTITY(1,1) NOT NULL,
    date_g DATE NOT NULL,
    date_j VARCHAR(10) NOT NULL,
    open_value DECIMAL(18,0) NULL,
    low_value DECIMAL(18,0) NULL,
    high_value DECIMAL(18,0) NULL,
    close_value DECIMAL(18,0) NULL,

    CONSTRAINT PK_usd_official_rates
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_usd_official_rates_date_g
        UNIQUE (date_g)
);
GO


CREATE TABLE dbo.tehran_stock_indices (
    id INT IDENTITY(1,1) NOT NULL,
    date_g DATE NOT NULL,
    date_j VARCHAR(10) NOT NULL,
    low_value DECIMAL(18,0) NULL,
    high_value DECIMAL(18,0) NULL,
    close_value DECIMAL(18,0) NULL,

    CONSTRAINT PK_tehran_stock_indices
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_tehran_stock_indices_date_g
        UNIQUE (date_g)
);
GO


/* ============================================================
   2. dbo - CPI / Inflation Tables
   ============================================================ */

CREATE TABLE dbo.monthly_cpi_main_group (
    id INT IDENTITY(1,1) NOT NULL,
    group_code VARCHAR(20) NULL,
    group_name_fa NVARCHAR(1000) NOT NULL,
    group_name_en NVARCHAR(1000) NOT NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    value DECIMAL(18,4) NULL,
    load_timestamp DATETIME2(7) NOT NULL,
    date_j NVARCHAR(20) NULL,
    date_g DATE NULL,

    CONSTRAINT PK_monthly_cpi_main_group
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_monthly_cpi_main_group_period
        UNIQUE (group_code, year, month)
);
GO


CREATE TABLE dbo.monthly_inflation_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_code VARCHAR(20) NULL,
    group_name_fa NVARCHAR(1000) NULL,
    group_name_en NVARCHAR(1000) NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    value DECIMAL(18,6) NULL,
    load_timestamp DATETIME2(7) NOT NULL,
    date_j NVARCHAR(20) NULL,
    date_g DATE NULL,

    CONSTRAINT PK_monthly_inflation_main_group
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_monthly_inflation_main_group_period
        UNIQUE (group_code, year, month)
);
GO


CREATE TABLE dbo.monthly_point_inflation_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_code VARCHAR(20) NULL,
    group_name_fa NVARCHAR(1000) NULL,
    group_name_en NVARCHAR(1000) NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    value DECIMAL(18,6) NULL,
    load_timestamp DATETIME2(7) NOT NULL,
    date_j NVARCHAR(20) NULL,
    date_g DATE NULL,

    CONSTRAINT PK_monthly_point_inflation_main_group
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_monthly_point_inflation_main_group_period
        UNIQUE (group_code, year, month)
);
GO


CREATE TABLE dbo.monthly_annual_inflation_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_code VARCHAR(20) NULL,
    group_name_fa NVARCHAR(1000) NULL,
    group_name_en NVARCHAR(1000) NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    value DECIMAL(18,6) NULL,
    load_timestamp DATETIME2(7) NOT NULL,
    date_j NVARCHAR(20) NULL,
    date_g DATE NULL,

    CONSTRAINT PK_monthly_annual_inflation_main_group
        PRIMARY KEY CLUSTERED (id),

    CONSTRAINT UQ_monthly_annual_inflation_main_group_period
        UNIQUE (group_code, year, month)
);
GO


/* ============================================================
   3. dbo - Metadata Tables
   ============================================================ */

CREATE TABLE dbo.cpi_dataset_info (
    dataset_id TINYINT NOT NULL,
    table_name SYSNAME NOT NULL,
    dataset_description NVARCHAR(2000) NOT NULL,

    CONSTRAINT PK_cpi_dataset_info
        PRIMARY KEY CLUSTERED (dataset_id)
);
GO


CREATE TABLE dbo.cpi_group_mapping (
    mapping_id INT IDENTITY(1,1) NOT NULL,
    group_name_fa NVARCHAR(1000) NOT NULL,
    group_code VARCHAR(20) NULL,
    group_name_en NVARCHAR(1000) NOT NULL,

    CONSTRAINT PK_cpi_group_mapping
        PRIMARY KEY CLUSTERED (mapping_id)
);
GO


CREATE TABLE dbo.data_sources
(
    source_id INT IDENTITY(1,1) NOT NULL,
    source_name NVARCHAR(200) NOT NULL,
    publisher_organization NVARCHAR(400) NULL,
    parent_organization NVARCHAR(400) NULL,
    access_method NVARCHAR(200) NULL,
    source_url NVARCHAR(2000) NULL,
    data_format NVARCHAR(100) NULL,
    description NVARCHAR(2000) NULL,

    CONSTRAINT PK_data_sources
        PRIMARY KEY CLUSTERED (source_id)
);
GO

CREATE TABLE dbo.indicator_sources
(
    indicator_id INT IDENTITY(1,1) NOT NULL,
    source_id INT NOT NULL,
    indicator_name NVARCHAR(400) NOT NULL,
    data_url NVARCHAR(2000) NULL,
    table_name NVARCHAR(256) NOT NULL,
    publication_frequency NVARCHAR(200) NULL,
    five_years_history BIT NOT NULL,
    value_column NVARCHAR(100) NULL,
    dimension_column NVARCHAR(256) NULL,
    description NVARCHAR(2000) NULL,


    CONSTRAINT PK_indicator_sources
        PRIMARY KEY CLUSTERED (indicator_id),

    CONSTRAINT FK_indicator_sources_data_sources
        FOREIGN KEY (source_id)
        REFERENCES dbo.data_sources (source_id)
);
GO

/* ============================================================
   4. raw - Market Data Tables
   ============================================================ */

CREATE TABLE raw.brent_oil_prices (
    open_value VARCHAR(100) NULL,
    low_value VARCHAR(100) NULL,
    high_value VARCHAR(100) NULL,
    close_value VARCHAR(100) NULL,
    change_value VARCHAR(100) NULL,
    change_percent VARCHAR(100) NULL,
    date_gregorian VARCHAR(100) NULL,
    date_jalali VARCHAR(100) NULL,
    load_timestamp DATETIME2(7) NULL
);
GO


CREATE TABLE raw.gold_prices_18k (
    open_value VARCHAR(100) NULL,
    low_value VARCHAR(100) NULL,
    high_value VARCHAR(100) NULL,
    close_value VARCHAR(100) NULL,
    change_value VARCHAR(100) NULL,
    change_percent VARCHAR(100) NULL,
    date_gregorian VARCHAR(100) NULL,
    date_jalali VARCHAR(100) NULL,
    load_timestamp DATETIME2(7) NULL
);
GO


CREATE TABLE raw.gold_prices_global (
    open_value VARCHAR(100) NULL,
    low_value VARCHAR(100) NULL,
    high_value VARCHAR(100) NULL,
    close_value VARCHAR(100) NULL,
    change_value VARCHAR(100) NULL,
    change_percent VARCHAR(100) NULL,
    date_gregorian VARCHAR(100) NULL,
    date_jalali VARCHAR(100) NULL,
    load_timestamp DATETIME2(7) NULL
);
GO


CREATE TABLE raw.usd_free_market_rates (
    open_value VARCHAR(100) NULL,
    low_value VARCHAR(100) NULL,
    high_value VARCHAR(100) NULL,
    close_value VARCHAR(100) NULL,
    change_value VARCHAR(100) NULL,
    change_percent VARCHAR(100) NULL,
    date_gregorian VARCHAR(100) NULL,
    date_jalali VARCHAR(100) NULL,
    load_timestamp DATETIME2(7) NULL
);
GO


CREATE TABLE raw.usd_official_rates (
    open_value VARCHAR(100) NULL,
    low_value VARCHAR(100) NULL,
    high_value VARCHAR(100) NULL,
    close_value VARCHAR(100) NULL,
    change_value VARCHAR(100) NULL,
    change_percent VARCHAR(100) NULL,
    date_gregorian VARCHAR(100) NULL,
    date_jalali VARCHAR(100) NULL,
    load_timestamp DATETIME2(7) NULL
);
GO


CREATE TABLE raw.tehran_stock_indices (
    date_g DATE NULL,
    date_j VARCHAR(100) NULL,
    close_value VARCHAR(100) NULL,
    low_value VARCHAR(100) NULL,
    high_value VARCHAR(100) NULL,
    load_timestamp DATETIME2(7) NULL
);
GO


/* ============================================================
   5. raw - CPI / Inflation Tables
   ============================================================ */

CREATE TABLE raw.monthly_cpi_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_name NVARCHAR(1000) NOT NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    raw_value NVARCHAR(200) NULL,
    load_timestamp DATETIME2(7) NOT NULL,

    CONSTRAINT PK_raw_monthly_cpi_main_group
        PRIMARY KEY CLUSTERED (id)
);
GO


CREATE TABLE raw.monthly_inflation_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_name NVARCHAR(1000) NOT NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    raw_value NVARCHAR(200) NULL,
    load_timestamp DATETIME2(7) NOT NULL,

    CONSTRAINT PK_raw_monthly_inflation_main_group
        PRIMARY KEY CLUSTERED (id)
);
GO


CREATE TABLE raw.monthly_point_inflation_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_name NVARCHAR(1000) NOT NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    raw_value NVARCHAR(200) NULL,
    load_timestamp DATETIME2(7) NOT NULL,

    CONSTRAINT PK_raw_monthly_point_inflation_main_group
        PRIMARY KEY CLUSTERED (id)
);
GO


CREATE TABLE raw.monthly_annual_inflation_main_group (
    id BIGINT IDENTITY(1,1) NOT NULL,
    group_name NVARCHAR(1000) NOT NULL,
    year SMALLINT NOT NULL,
    month TINYINT NOT NULL,
    raw_value NVARCHAR(200) NULL,
    load_timestamp DATETIME2(7) NOT NULL,

    CONSTRAINT PK_raw_monthly_annual_inflation_main_group
        PRIMARY KEY CLUSTERED (id)
);
GO