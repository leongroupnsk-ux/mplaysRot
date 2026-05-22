# 📁 Структура проекта Attribly Ads + AI

## Полный мап файлов и директорий

```
/Users/nikitaosepkov/Desktop/клон mplays/
│
├── docs/
│   ├── openapi.yaml                          ← Main API specification
│   └── TZ/                                    ← НОВОЕ: Documentation для Ads + AI
│       ├── README.md                         ← Overview и Quick Links
│       ├── SPEC_v1.0.md                      ← Полное техническое задание
│       ├── ARCHITECTURE.md                   ← Архитектура и Data Flows
│       ├── DEVELOPMENT_PLAN.md               ← План разработки по фазам
│       ├── CHECKLIST.md                      ← Чек-лист для команды
│       └── QUICK_START.md                    ← Быстрый старт
│
├── services/
│   │
│   ├── api-gateway/                          ← Существующий: Main API
│   │   ├── app/
│   │   ├── alembic/
│   │   ├── migrations/
│   │   ├── tests/
│   │   └── requirements.txt
│   │
│   ├── ads-integrations/                     ← НОВОЕ: Ads Platform Integrations
│   │   ├── __init__.py
│   │   ├── main.py                           ← FastAPI app entry point
│   │   ├── config.py                         ← Configuration & Settings
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── integrations.py               ← OAuth, подключение кабинетов
│   │   │   ├── audiences.py                  ← Look-alike аудитории
│   │   │   └── performance.py                ← Unified analytics
│   │   │
│   │   ├── adapters/                         ← [TODO Phase 2-3]
│   │   │   ├── __init__.py
│   │   │   ├── base.py                       ← Abstract base adapter
│   │   │   ├── yandex_direct.py              ← [Phase 2]
│   │   │   ├── yandex_direct_api.py          ← API client
│   │   │   ├── vk_ads.py                     ← [Phase 3]
│   │   │   ├── vk_ads_api.py
│   │   │   ├── telegram_ads.py               ← [Phase 5]
│   │   │   ├── telegram_ads_api.py
│   │   │   ├── vk_blogger.py                 ← [Phase 5]
│   │   │   └── vk_blogger_api.py
│   │   │
│   │   ├── tasks/                            ← [TODO Phase 2]
│   │   │   ├── __init__.py
│   │   │   ├── sync_tasks.py                 ← Celery tasks для синхронизации
│   │   │   └── scheduler.py                  ← Celery beat расписание
│   │   │
│   │   ├── models/                           ← [TODO Phase 1]
│   │   │   ├── __init__.py
│   │   │   ├── integration.py
│   │   │   ├── campaign.py
│   │   │   ├── performance.py
│   │   │   └── audience.py
│   │   │
│   │   ├── utils/                            ← [TODO Phase 1]
│   │   │   ├── __init__.py
│   │   │   ├── oauth.py                      ← OAuth helpers
│   │   │   ├── crypto.py                     ← AES-256-GCM encryption
│   │   │   ├── validators.py
│   │   │   └── constants.py
│   │   │
│   │   ├── tests/                            ← [TODO Phase 1]
│   │   │   ├── __init__.py
│   │   │   ├── unit/
│   │   │   │   ├── test_oauth.py
│   │   │   │   ├── test_crypto.py
│   │   │   │   └── test_models.py
│   │   │   ├── integration/
│   │   │   │   ├── test_yandex_direct_flow.py
│   │   │   │   └── test_vk_ads_flow.py
│   │   │   └── fixtures.py
│   │   │
│   │   ├── requirements.txt                  ← Dependencies
│   │   └── .env.example                      ← Example environment variables
│   │
│   ├── ml-attribution/                       ← НОВОЕ: ML Attribution Service
│   │   ├── __init__.py
│   │   ├── main.py                           ← FastAPI app entry point
│   │   ├── config.py                         ← Configuration & Settings
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── attribution.py                ← Inference endpoints
│   │   │   └── models.py                     ← Model management
│   │   │
│   │   ├── ml/                               ← [TODO Phase 4]
│   │   │   ├── __init__.py
│   │   │   ├── trainer.py                    ← CatBoost training
│   │   │   ├── features.py                   ← Feature engineering
│   │   │   ├── predictor.py                  ← ONNX inference
│   │   │   ├── data_loader.py                ← Load from PostgreSQL/ClickHouse
│   │   │   └── evaluator.py                  ← Model evaluation
│   │   │
│   │   ├── models/                           ← [TODO Phase 1]
│   │   │   ├── __init__.py
│   │   │   ├── ml_model.py
│   │   │   └── attributed_order.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── constants.py
│   │   │
│   │   ├── tests/                            ← [TODO Phase 4]
│   │   │   ├── __init__.py
│   │   │   ├── unit/
│   │   │   │   ├── test_feature_engineering.py
│   │   │   │   ├── test_predictor.py
│   │   │   │   └── test_trainer.py
│   │   │   └── integration/
│   │   │       └── test_attribution_flow.py
│   │   │
│   │   ├── models_storage/                   ← [Phase 4]
│   │   │   ├── wildberries/
│   │   │   │   ├── v1.onnx                   ← Trained ONNX model
│   │   │   │   └── metadata.json             ← Model metadata
│   │   │   └── amazon/                       ← Future
│   │   │
│   │   ├── requirements.txt                  ← Dependencies
│   │   └── .env.example
│   │
│   ├── ai-assistant/                         ← НОВОЕ: AI Assistant Service
│   │   ├── __init__.py
│   │   ├── main.py                           ← FastAPI app entry point
│   │   ├── config.py                         ← Configuration & Settings
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── assistant.py                  ← AI query endpoints
│   │   │
│   │   ├── services/                         ← [TODO Phase 5]
│   │   │   ├── __init__.py
│   │   │   ├── openai_proxy.py               ← OpenAI API wrapper
│   │   │   ├── context_builder.py            ← Build context for prompt
│   │   │   ├── rate_limiter.py               ← Tier-based rate limiting
│   │   │   └── cache.py                      ← Redis caching
│   │   │
│   │   ├── models/                           ← [TODO Phase 1]
│   │   │   ├── __init__.py
│   │   │   └── ai_query.py
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── constants.py
│   │   │   └── validators.py
│   │   │
│   │   ├── tests/                            ← [TODO Phase 5]
│   │   │   ├── __init__.py
│   │   │   ├── unit/
│   │   │   │   ├── test_openai_proxy.py
│   │   │   │   ├── test_context_builder.py
│   │   │   │   └── test_rate_limiter.py
│   │   │   └── integration/
│   │   │       └── test_ai_flow.py
│   │   │
│   │   ├── requirements.txt                  ← Dependencies
│   │   └── .env.example
│   │
│   ├── auth/                                 ← Пусто (заготовка)
│   ├── etl/                                  ← Существующий
│   ├── ingestion/                            ← Существующий
│   ├── ml/                                   ← Существующий (отличается от ml-attribution)
│   ├── notifications/                        ← Существующий
│   ├── reporting/                            ← Существующий
│   ├── segmentation/                         ← Существующий
│   └── tracking/                             ← Существующий
│
├── data/
│   ├── migrations/
│   │   ├── 001_init_postgres.sql
│   │   ├── 002_add_utm_trax_id.sql
│   │   ├── 003_anomaly_log_enrich.sql
│   │   └── 004_add_ads_integrations_schema.py ← НОВОЕ: Миграция БД
│   └── schemas/
│       └── clickhouse/
│           ├── 001_init_clickhouse.sql
│           ├── 002_add_utm_trax_id.sql
│           └── 003_anomaly_log_enrich.sql
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.node
│   │   ├── Dockerfile.python
│   │   ├── Dockerfile.ads-integrations         ← НОВОЕ
│   │   ├── Dockerfile.ml-attribution           ← НОВОЕ
│   │   ├── Dockerfile.ai-assistant             ← НОВОЕ
│   │   ├── prometheus.yml
│   │   └── nginx.conf
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   ├── helm/
│   └── k8s/
│       ├── kustomization.yaml
│       ├── namespace.yaml
│       ├── configmaps/
│       ├── deployments/
│       │   ├── ads-integrations.yaml           ← НОВОЕ
│       │   ├── ml-attribution.yaml             ← НОВОЕ
│       │   └── ai-assistant.yaml               ← НОВОЕ
│       ├── hpa/
│       ├── ingress/
│       ├── secrets/
│       └── services/
│
├── frontend/                                  ← Существующий (React)
│   ├── src/
│   ├── public/
│   ├── e2e/
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml                         ← Updated с новыми сервисами
├── .env                                       ← Runtime environment (локально)
├── .env.example                               ← Template
├── .gitignore
├── README.md                                  ← Main project README
└── (altri файлы проекта)
```

---

## 📊 Ключевые директории по фазам разработки

### Фаза 1: Infrastructure Setup

**Файлы для создания:**
```
services/ads-integrations/models/ ❌
services/ads-integrations/utils/ ❌
services/ads-integrations/tests/unit/ ❌
services/ml-attribution/models/ ❌
services/ai-assistant/models/ ❌
data/migrations/004_add_ads_integrations_schema.py ✅
infra/docker/Dockerfile.* ❌
infra/k8s/deployments/*.yaml ❌
```

### Фаза 2: Yandex Direct Integration

**Файлы для создания:**
```
services/ads-integrations/adapters/yandex_direct.py ❌
services/ads-integrations/adapters/yandex_direct_api.py ❌
services/ads-integrations/tasks/sync_tasks.py ❌
services/ads-integrations/tests/integration/test_yandex_direct_flow.py ❌
```

### Фаза 3: VK Ads Integration

**Файлы для создания:**
```
services/ads-integrations/adapters/vk_ads.py ❌
services/ads-integrations/adapters/vk_ads_api.py ❌
services/ads-integrations/tests/integration/test_vk_ads_flow.py ❌
```

### Фаза 4: ML Attribution

**Файлы для создания:**
```
services/ml-attribution/ml/trainer.py ❌
services/ml-attribution/ml/features.py ❌
services/ml-attribution/ml/predictor.py ❌
services/ml-attribution/models_storage/wildberries/ ❌
services/ml-attribution/tests/unit/test_*.py ❌
services/ml-attribution/tests/integration/test_attribution_flow.py ❌
```

### Фаза 5: AI Assistant

**Файлы для создания:**
```
services/ai-assistant/services/openai_proxy.py ❌
services/ai-assistant/services/context_builder.py ❌
services/ai-assistant/services/rate_limiter.py ❌
services/ai-assistant/tests/* ❌
```

---

## 🔄 Data Flow по структуре

### Flow 1: Ads Statistics Collection

```
Celery Task (sync_tasks.py)
    ↓
Adapter (yandex_direct.py)
    ↓
API Client (yandex_direct_api.py)
    ↓
Models (models/performance.py)
    ↓
PostgreSQL (ad_performance table)
    ↓
ClickHouse (via CDC / materialized view)
    ↓
Frontend API Response
```

### Flow 2: Order Attribution

```
WB Webhook
    ↓
ML Service routers/attribution.py
    ↓
Predictor (ml/predictor.py)
    ↓
CatBoost Model (models_storage/wildberries/v1.onnx)
    ↓
Model (models/attributed_order.py)
    ↓
PostgreSQL (attributed_orders table)
```

### Flow 3: AI Query

```
User Query
    ↓
AI Assistant (routers/assistant.py)
    ↓
Context Builder (services/context_builder.py)
    ↓
Rate Limiter (services/rate_limiter.py)
    ↓
OpenAI Proxy (services/openai_proxy.py)
    ↓
OpenAI API
    ↓
Response + Cache (Redis)
```

---

## 📦 Файлы, которые нужно создать в Фазе 1

**Priority: HIGH (Must have)**
- [ ] `services/ads-integrations/models/`
- [ ] `services/ads-integrations/utils/oauth.py`
- [ ] `services/ads-integrations/utils/crypto.py`
- [ ] `services/ml-attribution/models/`
- [ ] `services/ai-assistant/models/`
- [ ] `services/ads-integrations/tests/unit/`
- [ ] `infra/docker/Dockerfile.ads-integrations`
- [ ] `infra/docker/Dockerfile.ml-attribution`
- [ ] `infra/docker/Dockerfile.ai-assistant`

**Priority: MEDIUM (Should have)**
- [ ] `services/ads-integrations/adapters/base.py`
- [ ] `infra/k8s/deployments/*.yaml`
- [ ] CI/CD workflows

---

## ✅ Файлы уже готовы (Фаза 0)

- ✅ `docs/TZ/SPEC_v1.0.md`
- ✅ `docs/TZ/ARCHITECTURE.md`
- ✅ `docs/TZ/DEVELOPMENT_PLAN.md`
- ✅ `docs/TZ/CHECKLIST.md`
- ✅ `docs/TZ/README.md`
- ✅ `docs/TZ/QUICK_START.md`
- ✅ `data/migrations/004_add_ads_integrations_schema.py`
- ✅ `services/ads-integrations/main.py`
- ✅ `services/ads-integrations/config.py`
- ✅ `services/ads-integrations/routers/*.py`
- ✅ `services/ads-integrations/requirements.txt`
- ✅ `services/ml-attribution/main.py`
- ✅ `services/ml-attribution/config.py`
- ✅ `services/ml-attribution/routers/*.py`
- ✅ `services/ml-attribution/requirements.txt`
- ✅ `services/ai-assistant/main.py`
- ✅ `services/ai-assistant/config.py`
- ✅ `services/ai-assistant/routers/*.py`
- ✅ `services/ai-assistant/requirements.txt`

---

## 🎯 Next Steps

1. **Скопируйте этот файл** в Wiki или документацию проекта
2. **Используйте как reference** при создании новых файлов
3. **Обновляйте при добавлении** новых компонентов
4. **Следуйте [QUICK_START.md](QUICK_START.md)** для локального запуска

---

**Структура готова к разработке! 🚀**
