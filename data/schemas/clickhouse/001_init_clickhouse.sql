-- ─── ClickHouse: Аналитические таблицы Attribly ───────────────────────────────
-- Движок MergeTree с партиционированием по месяцу — стандарт для аналитических
-- событий с высоким write throughput.

-- ─── Клики (сырые события с трекинг-пикселя) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS clicks
(
    event_id        String,
    trax_id         String,
    campaign_id     String,
    user_id         String,       -- хеш владельца магазина (не покупателя!)
    -- Обезличенный fingerprint посетителя (SHA-256 ip+ua+date)
    visitor_hash    String,
    ts              DateTime64(3, 'UTC'),
    ip_hash         FixedString(64),  -- SHA-256, не хранится открыто
    device_type     LowCardinality(String),   -- desktop/mobile/tablet
    os              LowCardinality(String),
    browser         LowCardinality(String),
    country         LowCardinality(String),
    region          String,
    referrer_domain String,
    ad_platform     LowCardinality(String),
    marketplace     LowCardinality(String)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ts)
ORDER BY (campaign_id, trax_id, ts)
TTL toDateTime(ts) + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- ─── Воронка-события (избранное, корзина) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS funnel_events
(
    event_id        String,
    trax_id         String,
    campaign_id     String,
    visitor_hash    String,
    event_type      LowCardinality(String),  -- 'favorite'|'cart_add'|'cart_remove'
    marketplace     LowCardinality(String),
    product_id      String,
    ts              DateTime64(3, 'UTC')
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ts)
ORDER BY (campaign_id, visitor_hash, ts)
TTL toDateTime(ts) + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- ─── Заказы из маркетплейсов ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS marketplace_orders
(
    order_id            String,
    marketplace         LowCardinality(String),
    user_id             String,        -- хеш владельца магазина
    product_id          String,
    sku                 String,
    quantity            UInt32,
    order_amount        Decimal(12, 2),
    currency            FixedString(3) DEFAULT 'RUB',
    order_status        LowCardinality(String),  -- confirmed/cancelled/delivered
    ordered_at          DateTime64(3, 'UTC'),
    delivered_at        DateTime64(3, 'UTC'),
    -- Дополнительно для Amazon
    brand_referral_bonus Decimal(10, 2) DEFAULT 0,
    -- Заполняется ETL-пайплайном после атрибуции
    attributed_trax_id  String DEFAULT '',
    attributed_campaign_id String DEFAULT ''
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ordered_at)
ORDER BY (marketplace, user_id, ordered_at)
TTL toDateTime(ordered_at) + INTERVAL 3 YEAR
SETTINGS index_granularity = 8192;

-- ─── Статистика из рекламных кабинетов ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS ad_stats
(
    stat_date       Date,
    ad_platform     LowCardinality(String),
    user_id         String,
    campaign_id     String,         -- внутренний campaign_id Attribly
    external_campaign_id String,    -- ID в рекламном кабинете
    external_ad_id  String,         -- ID объявления/группы
    ad_name         String,
    impressions     UInt64,
    clicks          UInt64,
    spend           Decimal(12, 2),
    currency        FixedString(3) DEFAULT 'RUB',
    ctr             Float64,
    cpc             Decimal(10, 4),
    -- Конверсии, если кабинет отдаёт (Яндекс.Директ)
    conversions     UInt32 DEFAULT 0,
    conversion_value Decimal(12, 2) DEFAULT 0
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (ad_platform, user_id, campaign_id, stat_date)
SETTINGS index_granularity = 8192;

-- ─── Результаты атрибуции (выход ML-модели) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS attributions
(
    attribution_id      String,
    order_id            String,
    marketplace         LowCardinality(String),
    campaign_id         String,
    trax_id             String,
    ad_platform         LowCardinality(String),
    user_id             String,
    product_id          String,
    order_amount        Decimal(12, 2),
    click_at            DateTime64(3, 'UTC'),
    order_at            DateTime64(3, 'UTC'),
    -- Разница в часах между кликом и заказом
    hours_to_order      Float32,
    -- Метод и уверенность модели
    attribution_method  LowCardinality(String),  -- 'strict'|'probabilistic'
    confidence          Float32,       -- 0.0–1.0, только для probabilistic
    model_version       String,
    attributed_at       DateTime64(3, 'UTC') DEFAULT now64()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(order_at)
ORDER BY (campaign_id, order_at, trax_id)
SETTINGS index_granularity = 8192;

-- ─── ML-признаки для переобучения (Feature Store) ────────────────────────────
CREATE TABLE IF NOT EXISTS attribution_features
(
    feature_date    Date,
    trax_id         String,
    campaign_id     String,
    ad_platform     LowCardinality(String),
    marketplace     LowCardinality(String),
    click_at        DateTime64(3, 'UTC'),
    -- Признаки модели
    hours_since_click   Float32,
    geo_match           UInt8,   -- 1/0: совпадение региона клика и заказа
    device_match        UInt8,   -- 1/0: совпадение устройства
    product_match       UInt8,   -- 1/0: совпадение артикула
    platform_hist_rate  Float32, -- историческая конверсия этой площадки
    -- Метка: был ли подтверждён заказ (для обучения)
    label               UInt8,
    is_confirmed        UInt8 DEFAULT 0  -- подтверждено пользователем вручную
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(feature_date)
ORDER BY (campaign_id, feature_date, trax_id)
TTL toDateTime(toDateTime(feature_date)) + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ─── Материализованные агрегаты по кампаниям (дневной срез) ──────────────────
CREATE TABLE IF NOT EXISTS campaign_daily_stats
(
    stat_date           Date,
    campaign_id         String,
    ad_platform         LowCardinality(String),
    marketplace         LowCardinality(String),
    user_id             String,
    -- Трафик
    clicks              UInt64,
    unique_visitors     UInt64,
    -- Воронка
    favorites           UInt32,
    cart_adds           UInt32,
    -- Атрибутированные результаты
    attributed_orders   UInt32,
    attributed_revenue  Decimal(14, 2),
    -- Рекламные расходы (join с ad_stats)
    spend               Decimal(12, 2),
    -- Расчётные метрики
    roas                Float64,     -- attributed_revenue / spend
    cpo                 Float64,     -- spend / attributed_orders
    click_to_order_rate Float64
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(stat_date)
ORDER BY (campaign_id, stat_date)
SETTINGS index_granularity = 8192;

-- ─── Materialized View: авто-заполнение campaign_daily_stats из кликов ────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_clicks_to_daily_stats
TO campaign_daily_stats
AS
SELECT
    toDate(ts)                      AS stat_date,
    campaign_id,
    ad_platform,
    marketplace,
    user_id,
    count()                         AS clicks,
    uniqExact(visitor_hash)         AS unique_visitors,
    0                               AS favorites,
    0                               AS cart_adds,
    0                               AS attributed_orders,
    0                               AS attributed_revenue,
    0                               AS spend,
    0                               AS roas,
    0                               AS cpo,
    0                               AS click_to_order_rate
FROM clicks
GROUP BY stat_date, campaign_id, ad_platform, marketplace, user_id;

-- ─── Materialized View: воронка-события в daily_stats ────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_funnel_to_daily_stats
TO campaign_daily_stats
AS
SELECT
    toDate(ts)                              AS stat_date,
    campaign_id,
    '' AS ad_platform,
    marketplace,
    ''  AS user_id,
    0   AS clicks,
    0   AS unique_visitors,
    countIf(event_type = 'favorite')        AS favorites,
    countIf(event_type = 'cart_add')        AS cart_adds,
    0 AS attributed_orders,
    0 AS attributed_revenue,
    0 AS spend,
    0 AS roas,
    0 AS cpo,
    0 AS click_to_order_rate
FROM funnel_events
GROUP BY stat_date, campaign_id, marketplace;

-- ─── Таблица для детектора аномалий ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anomaly_log
(
    detected_at     DateTime64(3, 'UTC') DEFAULT now64(),
    campaign_id     String,
    metric          LowCardinality(String),  -- 'cpc'|'conversion_rate'|'roas'
    current_value   Float64,
    expected_value  Float64,
    deviation_pct   Float64,
    severity        LowCardinality(String),  -- 'warning'|'critical'
    notified        UInt8 DEFAULT 0
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(detected_at)
ORDER BY (campaign_id, detected_at)
TTL toDateTime(detected_at) + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;
