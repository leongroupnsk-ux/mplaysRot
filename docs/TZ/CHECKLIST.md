# ✅ Чек-лист для команды разработки

## Этап 0: Подготовка (ЗАВЕРШЕНО ✅)

### Документация
- ✅ Создано полное техническое задание (SPEC_v1.0.md)
- ✅ Описана архитектура (ARCHITECTURE.md)
- ✅ Разработан план по фазам (DEVELOPMENT_PLAN.md)
- ✅ Подготовлен README с быстрым стартом
- ✅ Создан этот чек-лист

### Структура проекта
- ✅ Директория `services/ads-integrations/`
- ✅ Директория `services/ml-attribution/`
- ✅ Директория `services/ai-assistant/`
- ✅ Основные файлы конфигурации и main.py для каждого сервиса
- ✅ Базовые роутеры (integrrations.py, audiences.py, performance.py)

### База данных
- ✅ Миграция Alembic (004_add_ads_integrations_schema.py) готова

---

## 🚀 Фаза 1: Инфраструктура (Неделя 1)

### Backend (Platform Engineer / DevOps)

- [ ] **1.1** Установить необходимые зависимости Python
  ```bash
  pip install -r services/ads-integrations/requirements.txt
  pip install -r services/ml-attribution/requirements.txt
  pip install -r services/ai-assistant/requirements.txt
  ```

- [ ] **1.2** Запустить миграцию БД
  ```bash
  cd services/api-gateway
  alembic upgrade head
  ```

- [ ] **1.3** Создать базовые модели SQLAlchemy в каждом микросервисе
  - `services/ads-integrations/models.py` (Integration, AdCampaign, AdPerformance)
  - `services/ml-attribution/models.py` (MlModel, AttributedOrder)
  - `services/ai-assistant/models.py` (AiQuery)

- [ ] **1.4** Реализовать OAuth utilities
  - `services/ads-integrations/utils/oauth.py` — OAuth state management, PKCE
  - `services/ads-integrations/utils/crypto.py` — AES-256-GCM encrypt/decrypt

- [ ] **1.5** Написать unit-тесты
  - `tests/unit/oauth_test.py`
  - `tests/unit/crypto_test.py`
  - `tests/unit/models_test.py`

- [ ] **1.6** Настроить Docker образы
  - Создать `Dockerfile.ads-integrations`
  - Создать `Dockerfile.ml-attribution`
  - Создать `Dockerfile.ai-assistant`
  - Обновить `docker-compose.yml`

- [ ] **1.7** Настроить CI/CD
  - GitHub Actions workflow для testing
  - Sonarqube intergration для quality gates
  - Registry для Docker образов

### QA

- [ ] **1.5a** Написать интеграционные тесты для OAuth flow (mock)
- [ ] **1.5b** Написать тесты для database migrations

### Frontend (Optional)

- [ ] **1.8** Подготовить UI компоненты для интеграций
  - Button "Connect to Yandex.Direct"
  - Modal с OAuth redirectом
  - Loading state для синхронизации

### DevOps

- [ ] **1.9** Развернуть новые контейнеры в staging
  ```bash
  docker compose -f docker-compose.staging.yml up -d
  ```

### Доставить к концу недели
- ✅ Все 3 микросервиса запущены и доступны на своих портах
- ✅ Health endpoints работают
- ✅ БД миграция применена
- ✅ Basic tests passed

---

## 📊 Фаза 2: Яндекс.Директ (Неделя 2-3)

### Backend

- [ ] **2.1** Реализовать OAuth-flow для Яндекс.Директ
  - Создать `services/ads-integrations/adapters/yandex_direct.py` (OAuth handler)
  - Endpoint: `POST /api/v1/integrations/yandex_direct/auth`
  - Endpoint: `GET /api/v1/integrations/yandex_direct/callback`
  - Сохранять encrypted токены в БД

- [ ] **2.2** Создать Yandex Direct API adapter
  - `services/ads-integrations/adapters/yandex_direct_api.py`
  - Методы: `get_campaigns()`, `get_statistics()`, `create_audience()`, etc.
  - Использовать HTTPS, handle rate limits

- [ ] **2.3** Реализовать сбор статистики
  - Создать `services/ads-integrations/tasks/yandex_direct_sync.py` (Celery task)
  - Ежедневный крон в 01:00 UTC
  - Сохранять в таблицу `ad_performance`

- [ ] **2.4** Реализовать Celery task
  - Зарегистрировать task в Celery
  - Добавить в celery-beat расписание
  - Логировать успехи/ошибки

- [ ] **2.5** Реализовать управление аудиториями
  - Endpoint: `POST /api/v1/audiences/lookalike/create`
  - Создавать look-alike сегменты в Яндекс.Директ
  - Сохранять metadata в БД

- [ ] **2.6** Написать интеграционные тесты
  - Mock Yandex.Direct API responses
  - Test OAuth flow
  - Test statistics collection
  - Test audience creation

### Frontend

- [ ] **2.7** Создать UI для подключения Яндекс.Директ
  - Страница "Integrations > Yandex Direct"
  - Button "Connect" → OAuth redirect → Callback
  - Display connection status
  - Manual "Sync Now" button

- [ ] **2.8** Создать analytics dashboard для Яндекс.Директ
  - Chart: Impressions, Clicks, Spend, Conversions (daily)
  - Table: Campaign-level stats
  - Filters: Date range, campaign

### QA

- [ ] **2.6** Интеграционные тесты
  - OAuth flow (happy path + error cases)
  - Statistics sync (verify data in DB)
  - Rate limit handling

### DevOps

- [ ] Monitoring dashboard для сервиса
- [ ] Alerting rules (sync failures, API errors)

### Доставить к концу недели 3
- ✅ Полная интеграция Яндекс.Директ
- ✅ Ежедневная синхронизация работает
- ✅ UI для подключения готов
- ✅ Analytics dashboard работает

---

## 💡 Фаза 3: VK Ads (Неделя 4-5)

### Backend

- [ ] **3.1-3.6** Повторить для VK Ads
  - `services/ads-integrations/adapters/vk_ads.py`
  - Endpoint: `POST /api/v1/integrations/vk_ads/auth`
  - Дополнительно: сбор демографических данных
  - Дополнительно: синхронизация товарных фидов

- [ ] **3.7** Написать интеграционные тесты

### Frontend

- [ ] **3.8** UI для VK Ads
  - Similar to Yandex.Direct
  - + Demographic breakdown (age, geo, device)
  - + Feed sync status

### Deliverable
- ✅ Dual-platform support (Яндекс.Директ + VK Ads)
- ✅ Unified analytics dashboard

---

## 🤖 Фаза 4: ML Attribution (Неделя 6-8)

### Data Science

- [ ] **4.1** Подготовить датасет для обучения
  - Собрать исторические данные о кликах и заказах WB
  - ~10K+ verified samples

- [ ] **4.2** Feature Engineering
  - time_diff (click to order)
  - geo_match
  - device_match
  - source_historical_conv_rate
  - clicks_from_same_ip
  - order_amount
  - day_of_week, hour_of_day

- [ ] **4.3** Обучить CatBoost модель
  - Hyperparams: iterations=500, depth=6, learning_rate=0.03
  - Train/test split 80/20
  - Measure AUC > 0.85

- [ ] **4.4** Конвертировать модель в ONNX

### Backend

- [ ] **4.5** Реализовать inference endpoint
  - `POST /api/v1/attribution/predict`
  - Load ONNX model
  - Extract features from request
  - Return probability score

- [ ] **4.6** Batch prediction для исторических заказов
  - `POST /api/v1/attribution/batch/predict`
  - Background task via Celery

- [ ] **4.7** Webhook для новых заказов WB
  - Integrate with WB API
  - Real-time attribution

- [ ] **4.9** Запланировать переобучение
  - Celery task, ежедневно в 02:00 UTC
  - Использовать верифицированные дані від користувачів

### Frontend

- [ ] **4.8** UI для верификации атрибуции
  - Table: Order ID, Predicted Click, Confidence, Actions
  - Actions: "Correct ✓", "Wrong ✗", "Not sure ?"
  - Feedback → training data

### QA

- [ ] **4.10** ML-специфичные тесты
  - Model accuracy validation
  - Feature engineering tests
  - Batch prediction tests

### Deliverable
- ✅ Working ML model (AUC > 0.85)
- ✅ Real-time attribution for new orders
- ✅ User feedback collection

---

## 🧠 Фаза 5: AI Assistant (Неделя 9-11)

### Backend

- [ ] **5.1.1** Context builder
  - Query WB warehouse API (stocks)
  - Query PostgreSQL (sales, returns last 7 days)
  - Query ad_performance (campaign stats)
  - Build Markdown-formatted context

- [ ] **5.1.2** OpenAI proxy
  - `services/ai-assistant/openai_proxy.py`
  - Handle API key, endpoint, model from config
  - Implement timeouts (15s)
  - Error handling, retries

- [ ] **5.1.3** Redis caching
  - Cache responses keyed by context hash + question
  - TTL: 1 hour

- [ ] **5.1.4** Audit logging
  - Log all queries to `ai_queries` table
  - Track tokens used, cost, cached

- [ ] **5.1.5** Rate limiting
  - Business tier: 50 queries/month
  - Enterprise tier: unlimited
  - User-based limits via Redis

- [ ] **5.1.7** Tests (mock OpenAI)
  - Mock OpenAI responses
  - Test context building
  - Test rate limiting

### Frontend

- [ ] **5.1.6** UI integration
  - Right panel in dashboard
  - Input field for question
  - Markdown display for answer
  - Spinner while loading
  - Usage stats (queries used / limit)

### Deliverable
- ✅ Fully functional AI Assistant
- ✅ Latency < 2s (with caching)
- ✅ Rate limiting working

### Telegram Ads (P1, 2 недели)

- [ ] **5.2.1-5.2.4** Реализовать Telegram Ads adapter
  - Similar to других платформ
  - Pixel tracking integration
  - Event collection

### VK Blogger (P2, 3 недели)

- [ ] **5.3.1-5.3.3** Реализовать VK Blogger adapter

---

## 📤 Фаза 6: Экспорт и BI (Неделя 12-13)

### Backend

- [ ] **6.1** CSV экспорт для атрибуции
  - `POST /api/v1/export/attribution`
  - Fields: trax_id, timestamp_click, timestamp_order, order_id, sku, revenue, source, campaign, confidence, verified
  - Return download link

- [ ] **6.2** CSV экспорт для логистики
  - `POST /api/v1/export/logistics`
  - Fields: warehouse_id, nm_id, chrt_id, size, stock_qty, sales_7d, returns_7d, return_rate, days_of_supply

- [ ] **6.3** Celery background job для больших экспортов
  - Generate CSV
  - Upload to S3
  - Send email with download link

- [ ] **6.4** Email notifications
  - Send when export is ready
  - Include presigned S3 URL

### Roadmap (Future)

- [ ] **6.5-6.6** Power BI / Tableau коннекторы (Phase 2)

### Frontend

- [ ] Export buttons in Analytics pages
- [ ] Download history

---

## 🎯 Метрики успеха

По окончании каждой фазы проверить:

### Фаза 1 ✅
- [ ] Все сервисы запущены и здоровы
- [ ] Health endpoints возвращают 200
- [ ] БД миграция применена успешно

### Фаза 2-3
- [ ] 100% data sync accuracy
- [ ] Сбор статистики без errors
- [ ] UI интуитивен и работает

### Фаза 4
- [ ] ML model AUC > 0.85
- [ ] Real-time inference latency < 500ms
- [ ] User feedback collection working

### Фаза 5
- [ ] AI Assistant latency < 2s (cached), < 15s (first call)
- [ ] Rate limiting enforced
- [ ] Audit logging in place

### Фаза 6
- [ ] Export works for 100K+ rows
- [ ] CSV format correct
- [ ] Email notifications sent

---

## 🔗 Ссылки на ресурсы

- **Полное ТЗ:** [docs/TZ/SPEC_v1.0.md](SPEC_v1.0.md)
- **Архитектура:** [docs/TZ/ARCHITECTURE.md](ARCHITECTURE.md)
- **План разработки:** [docs/TZ/DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
- **README:** [docs/TZ/README.md](README.md)
- **Миграции БД:** [data/migrations/004_add_ads_integrations_schema.py](../migrations/004_add_ads_integrations_schema.py)

---

## 📅 Статус

| Фаза | Статус | Ответственный | ETA |
| :--- | :---: | :--- | :--- |
| 0 (Подготовка) | ✅ Done | Tech Lead | - |
| 1 (Инфраструктура) | ⏳ To Do | Backend + DevOps | Неделя 1 |
| 2 (Яндекс.Директ) | ⏳ To Do | Backend + Frontend | Неделя 2-3 |
| 3 (VK Ads) | ⏳ To Do | Backend + Frontend | Неделя 4-5 |
| 4 (ML Attribution) | ⏳ To Do | DS + Backend | Неделя 6-8 |
| 5 (AI Assistant) | ⏳ To Do | Backend + Frontend | Неделя 9-11 |
| 6 (Export/BI) | ⏳ To Do | Backend | Неделя 12-13 |

**MVP Launch:** Конец недели 11  
**Phase 2 Start:** Неделя 12

---

## 🚨 Блокеры и риски

| Риск | Статус | Mitigation |
| :--- | :---: | :--- |
| API лимиты платформ | 🟡 Medium | Caching, batch requests, rate limiting |
| ML model training time | 🟡 Medium | Parallel processing, GPU if available |
| OpenAI API availability | 🟡 Medium | Graceful degradation, fallback responses |
| OAuth token expiry | 🔴 High | Automatic refresh, monitoring |

---

**Обновлено:** 6 мая 2026 г.  
**Ответственный:** Tech Lead  
**Версия:** 1.0
