# Архитектура модуля Атрибли Ads + AI

## Обзор системы

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vite)                           │
│                      http://localhost:3000                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼─────────┐  ┌──▼──────────┐  ┌─▼──────────────────┐
│  API Gateway    │  │  Auth       │  │  Ads Integration   │
│  :8000-8001     │  │  Service    │  │  Service (NEW)     │
│  (FastAPI)      │  │             │  │  :8004 (FastAPI)   │
└────────┬────────┘  └─────────────┘  └────────┬───────────┘
         │                                      │
         │                    ┌─────────────────┼──────────────┐
         │                    │                 │              │
    ┌────▼─────────────┐  ┌──▼──────────┐  ┌──▼────────┐  ┌──▼─────────┐
    │  PostgreSQL      │  │  ClickHouse │  │   Redis   │  │   Kafka    │
    │  :5432           │  │   :8123     │  │  :6379    │  │  :9092     │
    │  (Database)      │  │ (Analytics) │  │(Caching)  │  │(Events)    │
    └──────────────────┘  └─────────────┘  └───────────┘  └────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              ML Attribution Service (NEW)                         │
│                    :8005 (FastAPI)                               │
│  CatBoost model inference + training                             │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              AI Assistant Service (NEW)                           │
│                    :8006 (FastAPI)                               │
│  OpenAI-compatible API proxy                                      │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│              External Ad Platforms                                │
│  • Yandex.Direct (API v5)                                         │
│  • VK Ads (API)                                                   │
│  • Telegram Ads Platform                                          │
│  • VK Blogger API                                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Микросервисная архитектура

### 1. API Gateway (Существующий)
- Единая точка входа для клиентов
- Аутентификация/авторизация
- Rate limiting
- Логирование и мониторинг

### 2. Ads Integration Service (Новый)
**Порт:** 8004  
**Назначение:** Управление подключениями к рекламным платформам

**Основные компоненты:**
- OAuth handlers для каждой платформы
- Adapters (Yandex Direct, VK Ads, Telegram Ads, VK Blogger)
- Statistics collectors (async tasks via Celery)
- Audience managers (look-alike segment creation)
- DTO/Schema validation

**Таблицы БД:**
- `integrations` — OAuth-токены и статус подключений
- `ad_campaigns` — кампании из внешних платформ
- `ad_performance` — дневная статистика
- `lookalike_audiences` — управление look-alike сегментами

### 3. ML Attribution Service (Новый)
**Порт:** 8005  
**Назначение:** Вероятностная атрибуция заказов

**Основные компоненты:**
- CatBoost model loader (ONNX inference)
- Feature engineering pipeline
- Training scheduler (daily)
- Batch prediction endpoint
- User feedback collection

**Таблицы БД:**
- `ml_models` — версии обученных моделей
- `attributed_orders` — результаты атрибуции

**ClickHouse:**
- `tracking_events` — клики и события (быстрая аналитика)

### 4. AI Assistant Service (Новый)
**Порт:** 8006  
**Назначение:** OpenAI-powered рекомендации

**Основные компоненты:**
- Context builder (warehouse, sales, ads data)
- OpenAI proxy (с ограничениями по тарифам)
- Cache manager (Redis)
- Rate limiter по пользователям
- Query logger для аудита

**Таблицы БД:**
- `ai_queries` — лог всех запросов (для аудита)

## Потоки данных

### Flow 1: Сбор статистики рекламных кабинетов
```
Scheduled Task (Celery beat)
    ↓
Ads Integration Service
    ├─→ Yandex.Direct API (reports endpoint)
    ├─→ VK Ads API (statistics endpoint)
    ├─→ Telegram Ads API
    └─→ VK Blogger API
    ↓
PostgreSQL (ad_performance table)
    ↓
ClickHouse (fact_ad_stats materialized view)
    ↓
Frontend Dashboard (charts, tables)
```

### Flow 2: Order Attribution (WB)
```
WB API webhook (new order)
    ↓
ML Attribution Service
    ├─→ Query PostgreSQL: clicks за последние 24 часа
    ├─→ Extract features (time_diff, geo_match, device_match, etc.)
    ├─→ CatBoost model inference (ONNX runtime)
    └─→ Get probability score
    ↓
PostgreSQL (attributed_orders table)
    ├─→ confidence >= 0.7: auto-attributed
    └─→ confidence < 0.7: requires verification
    ↓
Frontend: User reviews and verifies
    ↓
Verified attribution → Training data for next retraining
```

### Flow 3: AI Assistant Query
```
User asks: "Какие размеры срочно пополнить?"
    ↓
AI Assistant Service
    ├─→ Check Redis cache (exact match)
    ├─→ If miss:
    │   ├─→ Query WB warehouse API (stocks)
    │   ├─→ Query PostgreSQL (sales, returns for last 7 days)
    │   ├─→ Query ad_performance (campaign stats)
    │   └─→ Build context prompt
    ├─→ Call OpenAI API (gpt-4o, temp=0.3)
    └─→ Cache result in Redis (1 hour TTL)
    ↓
Response in Markdown format
    ↓
Frontend: Display in right panel + log to DB
```

## Data Flow Integrations

### PostgreSQL Schema Additions
```sql
CREATE TABLE integrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    provider VARCHAR(50),  -- yandex_direct, vk_ads, telegram_ads, vk_blogger
    access_token BYTEA,    -- AES-256-GCM encrypted
    refresh_token BYTEA,   -- AES-256-GCM encrypted
    token_expires_at TIMESTAMP,
    status VARCHAR(20),    -- active, expired, revoked
    metadata JSONB,        -- provider-specific data
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Daily statistics per campaign
CREATE TABLE ad_performance (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL,
    date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spent NUMERIC(12,2) DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue NUMERIC(12,2) DEFAULT 0,
    ctr NUMERIC(5,4),
    cpc NUMERIC(10,2),
    roas NUMERIC(5,2),
    synced_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(campaign_id, date)
);

-- Order-to-click attribution
CREATE TABLE attributed_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL,
    marketplace VARCHAR(50),  -- wildberries, amazon
    trax_id VARCHAR(100),     -- link to click
    click_timestamp TIMESTAMP,
    order_timestamp TIMESTAMP NOT NULL,
    order_amount NUMERIC(12,2),
    confidence NUMERIC(5,4),  -- model probability
    verified BOOLEAN DEFAULT FALSE,
    model_version VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(order_id, marketplace)
);

-- AI query audit log
CREATE TABLE ai_queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    model_used VARCHAR(50) DEFAULT 'gpt-4o',
    tokens_used INTEGER,
    cost NUMERIC(10,4),
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### ClickHouse Schema Additions
```sql
-- Fast analytics for ad performance
CREATE TABLE tracking_events (
    event_id UUID,
    event_type String,  -- click, impression, conversion
    campaign_id String,
    provider String,
    timestamp DateTime,
    user_id String,
    utm_source String,
    utm_campaign String,
    utm_medium String,
    device_type String,
    geo String,
    trax_id String
)
ENGINE = MergeTree()
ORDER BY (provider, timestamp, campaign_id);

-- Materialized view for aggregated stats
CREATE MATERIALIZED VIEW ad_stats_daily AS
SELECT
    provider,
    campaign_id,
    toDate(timestamp) as date,
    countIf(event_type = 'impression') as impressions,
    countIf(event_type = 'click') as clicks,
    countIf(event_type = 'conversion') as conversions,
    count(DISTINCT user_id) as unique_users
FROM tracking_events
GROUP BY provider, campaign_id, date;
```

## Security Considerations

1. **Token Storage**
   - Все OAuth-токены шифруются AES-256-GCM перед сохранением в БД
   - Ключ шифрования хранится в переменных окружения
   - Автоматическое обновление refresh-токенов

2. **API Security**
   - Все эндпоинты требуют JWT-аутентификацию
   - Rate limiting на уровне пользователя
   - IP whitelisting для критичных операций

3. **Data Privacy**
   - Логирование всех административных действий
   - GDPR-compliance для пользовательских данных
   - Шифрование в транзите (HTTPS/TLS)

4. **AI Safety**
   - Лимиты по использованию OpenAI API (по тарифам)
   - Логирование всех AI-запросов для аудита
   - Фильтрация чувствительных данных в контексте

## Развёртывание (Docker Compose)

Новые сервисы добавлены в `docker-compose.yml`:

```yaml
ads-integrations:
  image: mplays-ads-integrations
  ports:
    - "8004:8004"
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    REDIS_PASSWORD: ${REDIS_PASSWORD}
  depends_on:
    - postgres
    - redis

ml-attribution:
  image: mplays-ml-attribution
  ports:
    - "8005:8005"
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
  depends_on:
    - postgres
    - clickhouse

ai-assistant:
  image: mplays-ai-assistant
  ports:
    - "8006:8006"
  environment:
    OPENAI_API_KEY: ${OPENAI_API_KEY}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  depends_on:
    - postgres
    - redis
```

## Мониторинг и логирование

Все сервисы экспортируют Prometheus метрики на `/metrics`:

```
# Ads Integration Service
ads_api_calls_total{provider="yandex_direct", endpoint="reports"}
ads_sync_duration_seconds{provider="vk_ads"}
ad_performance_records_synced{provider="telegram_ads"}

# ML Attribution Service
attribution_predictions_total{marketplace="wildberries"}
attribution_avg_confidence{confidence_bucket}
model_retraining_duration_seconds

# AI Assistant Service
ai_queries_total{model="gpt-4o"}
ai_query_latency_seconds
ai_tokens_used_total{tier="business"}
```

## Roadmap фаз

**Фаза 1 (Неделя 1-2):** Setup + Yandex.Direct  
**Фаза 2 (Неделя 3-4):** VK Ads + ML основы  
**Фаза 3 (Неделя 5-6):** ML training + AI Assistant  
**Фаза 4 (Неделя 7+):** Telegram Ads, VK Blogger, Fine-tuning
