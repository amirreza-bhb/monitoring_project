-------------------------------------------------------------
-- data sources insertion
-------------------------------------------------------------
INSERT INTO dbo.data_sources
(
    source_name,
    publisher_organization,
    parent_organization,
    access_method,
    source_url,
    data_format,
    description
)
VALUES
(
    N'شبکه اطلاع‌رسانی طلا، ارز و بورس (TGJU)',
    N'TGJU',
    NULL,
    N'API',
    N'https://www.tgju.org/',
    N'JSON',
    N'دریافت داده‌های شاخص‌های اقتصادی و مالی از طریق API'
),
(
    N'Iran CPI Data',
    N'مرکز آمار ایران',
    NULL,
    N'File',
    N'https://amar.org.ir/prices#app3105',
    N'Excel',
    N'دریافت داده‌های اقتصادی و آماری از طریق فایل‌های منتشرشده'
);
-------------------------------------------------------------
-- indicator sources insertion
-------------------------------------------------------------
INSERT INTO dbo.indicator_sources
(
    source_id,
    indicator_name,
    data_url,
    table_name,
    publication_frequency,
    five_years_history,
    description,
    value_column,
    dimension_column
)
VALUES
-- =========================================================
-- TGJU
-- =========================================================

(1, N'Brent Oil Price',
 N'https://api.tgju.org/v1/market/indicator/summary-table-data/energy-brent-oil',
 N'brent_oil_prices',
 N'Daily',
 1,
 N'Brent crude oil price',
 N'close_value',
 NULL),

(1, N'Gold Price 18K',
 N'https://api.tgju.org/v1/market/indicator/summary-table-data/geram18',
 N'gold_prices_18k',
 N'Daily',
 1,
 N'18-karat gold price',
 N'close_value',
 NULL),

(1, N'Global Gold Price',
 N'https://api.tgju.org/v1/market/indicator/summary-table-data/ons',
 N'gold_prices_global',
 N'Daily',
 1,
 N'Global gold price',
 N'close_value',
 NULL),

(1, N'USD Free Market Rate',
 N'https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl',
 N'usd_free_market_rates',
 N'Daily',
 1,
 N'US dollar free market exchange rate',
 N'close_value',
 NULL),

(1, N'USD Official Rate',
 N'https://api.tgju.org/v1/market/indicator/summary-table-data/bank_usd',
 N'usd_official_rates',
 N'Daily',
 1,
 N'US dollar official exchange rate',
 N'close_value',
 NULL),

(1, N'Tehran Stock Index',
 N'https://api.tgju.org/v1/stocks/instrument/history-data/%D8%B4-%DA%A9%D9%84-%D8%A8%D9%88%D8%B1%D8%B3',
 N'tehran_stock_indices',
 N'Daily',
 1,
 N'Tehran Stock Exchange overall index',
 N'close_value',
 NULL),

-- =========================================================
-- Iran CPI / Inflation
-- =========================================================

(2, N'Monthly CPI - Main Groups',
 N'https://amar.org.ir/prices#app3105',
 N'monthly_cpi_main_group',
 N'Monthly',
 1,
 N'Monthly Consumer Price Index by main expenditure groups',
 N'value',
 N'group_name_en'),

(2, N'Monthly Inflation - Main Groups',
 N'https://amar.org.ir/prices#app3105',
 N'monthly_inflation_main_group',
 N'Monthly',
 1,
 N'Monthly inflation rate by main expenditure groups',
 N'value',
 N'group_name_en'),

(2, N'Monthly Point-to-Point Inflation - Main Groups',
 N'https://amar.org.ir/prices#app3105',
 N'monthly_point_inflation_main_group',
 N'Monthly',
 1,
 N'Monthly point-to-point inflation rate by main expenditure groups',
 N'value',
 N'group_name_en'),

(2, N'Monthly Annual Inflation - Main Groups',
 N'https://amar.org.ir/prices#app3105',
 N'monthly_annual_inflation_main_group',
 N'Monthly',
 1,
 N'Monthly annual inflation rate by main expenditure groups',
 N'value',
 N'group_name_en');