# Модуль Интеграции Рекламных Кабинетов и AI/BI-систем (attribly-ads-ai)

Это comprehensive модуль для платформы Attribly, обеспечивающий интеграцию с основными рекламными платформами, ML-атрибуцию заказов и AI-ассистента на базе OpenAI.

## 📋 Содержание

- [Обзор](#обзор)
- [Структура проекта](#структура-проекта)
- [Быстрый старт](#быстрый-старт)
- [Микросервисы](#микросервисы)
- [API Документация](#api-документация)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Развёртывание](#развёртывание)

## 🎯 Обзор

### Что включает?

1. **Ads Integration Service** — интеграция с рекламными платформами
   - Яндекс.Директ (OAuth, статистика, аудитории)
   - VK Ads (OAuth, статистика, демография, фиды)
   - Telegram Ads (пиксель-трекинг)
   - VK Blogger (метрики публикаций)

2. **ML Attribution Service** — вероятностная атрибуция
   - CatBoost модель для Wildberries
   - Inference + Training pipeline
   - User feedback collection
   - Дневное переобучение

3. **AI Assistant Service** — ИИ-рекомендации
   - OpenAI-совместимый API proxy
   - Контекстная подсказка (warehouse, sales, ads)
   - Rate limiting по тарифам
   - Redis кеширование

4. **Export Service** (Roadmap) — выгрузка в BI
   - CSV экспорт атрибуции
   - CSV экспорт логистики
   - Power BI / Tableau коннекторы

### Ключевые возможности

- 🔐 Безопасное хранение OAuth-токенов (AES-256-GCM)
- 📊 Единый дашборд по всем рекламным кабинетам
- 🤖 Вероятностная атрибуция заказов WB/Amazon
- 🧠 AI-ассистент для логистики и маркетинга
- 📤 Экспорт для анализа в BI-системах
- 🔄 Автоматическая синхронизация по расписанию
- 📈 Prometheus метрики для мониторинга

## 📂 Структура проекта

```
services/
├── ads-integrations/          # Интеграция с рекламными платформами
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── integrations.py    # OAuth, подключение кабинетов
│   │   ├── audiences.py       # Look-alike аудитории
│   │   └── performance.py     # Unified analytics
│   ├── adapters/              # [TODO] Адаптеры для каждой платформы
│   │   ├── yandex_direct.py
│   │   ├── vk_ads.py
│   │   ├── telegram_ads.py
│   │   └── vk_blogger.py
│   ├── tasks/                 # [TODO] Celery задачи для синхронизации
│   └── requirements.txt
│
├── ml-attribution/            # ML-модель атрибуции
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── attribution.py     # Inference endpoint
│   │   └── models.py          # Model management
│   ├── ml/                    # [TODO] ML-логика
│   │   ├── trainer.py         # CatBoost training
│   │   ├── features.py        # Feature engineering
│   │   └── predictor.py       # ONNX inference
│   └── requirements.txt
│
└── ai-assistant/              # AI-ассистент
    ├── main.py
    ├── config.py
    ├── routers/
    │   └── assistant.py       # AI queries
    ├── openai_proxy.py        # [TODO] OpenAI wrapper
    └── requirements.txt

docs/TZ/
├── SPEC_v1.0.md              # ✅ Полное техническое задание
├── ARCHITECTURE.md           # ✅ Архитектура и потоки данных
├── DEVELOPMENT_PLAN.md       # ✅ План разработки по фазам
└── README.md                 # ✅ Этот файл

data/
└── migrations/
    └── 004_add_ads_integrations_schema.py  # ✅ Миграции БД
```

## 🚀 Быстрый старт

### Предварительные условия

- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 16
- ClickHouse 24.3
- Redis 7

### 1. Настройка окружения

```bash
# Скопировать переменные окружения
cp .env.example .env

# Добавить новые значения
OPENAI_API_KEY=sk-xxx...      # Для AI Assistant
YANDEX_DIRECT_CLIENT_ID=xxx   # Для Яндекс.Директ OAuth
YANDEX_DIRECT_CLIENT_SECRET=xxx
VK_SERVICE_TOKEN=xxx          # Для VK Ads/Blogger
```

### 2. Запуск Docker контейнеров

```bash
# Запустить все базы данных
docker compose up -d postgres clickhouse redis kafka

# Или запустить всё сразу (включая новые сервисы)
docker compose up -d

# Проверить статус
docker compose ps
```

### 3. Применить миграции

```bash
cd services/api-gateway
alembic upgrade head
```

### 4. Запустить микросервисы локально (dev mode)

```bash
# Терминал 1: Ads Integration Service
cd services/ads-integrations
pip install -r requirements.txt
python main.py

# Терминал 2: ML Attribution Service
cd services/ml-attribution
pip install -r requirements.txt
python main.py

# Терминал 3: AI Assistant Service
cd services/ai-assistant
pip install -r requirements.txt
python main.py
```

### 5. Проверить Health endpoints

```bash
curl http://localhost:8004/health      # Ads Integration
curl http://localhost:8005/health      # ML Attribution
curl http://localhost:8006/health      # AI Assistant
```

## 🔧 Микросервисы

| Сервис | Порт | Документация | Статус |
| :--- | :---: | :--- | :---: |
| Ads Integration | 8004 | `/docs` | ⏳ Phase 0 |
| ML Attribution | 8005 | `/docs` | ⏳ Phase 0 |
| AI Assistant | 8006 | `/docs` | ⏳ Phase 0 |

### Ads Integration Service (8004)

Управление подключениями к рекламным платформам.

**Основные endpoint'ы:**
```
POST   /api/v1/integrations/{provider}/auth      # Запустить OAuth
GET    /api/v1/integrations/{provider}/status    # Статус подключения
POST   /api/v1/integrations/{provider}/sync      # Ручная синхронизация
GET    /api/v1/analytics/performance             # Сводная статистика
POST   /api/v1/audiences/lookalike/create        # Look-alike сегмент
```

### ML Attribution Service (8005)

Вероятностная атрибуция заказов.

**Основные endpoint'ы:**
```
POST   /api/v1/attribution/predict                # Предсказать атрибуцию
POST   /api/v1/attribution/batch/predict          # Batch-предсказание
POST   /api/v1/attribution/verify                 # Верифицировать пользователем
GET    /api/v1/models/status                      # Статус модели
POST   /api/v1/models/retrain                     # Ручное переобучение
GET    /api/v1/models/features                    # Feature importance
```

### AI Assistant Service (8006)

ИИ-ассистент на базе OpenAI.

**Основные endpoint'ы:**
```
POST   /api/v1/ai/ask                             # Задать вопрос
GET    /api/v1/ai/history                         # История запросов
GET    /api/v1/ai/usage                           # Использованный лимит
```

## 📚 API Документация

Интерактивная документация доступна на `/docs` в каждом сервисе:
- http://localhost:8004/docs — Ads Integration
- http://localhost:8005/docs — ML Attribution
- http://localhost:8006/docs — AI Assistant

## 💻 Разработка

### Структура кода

```
adheres to:
- ✅ FastAPI best practices
- ✅ SQLAlchemy ORM patterns
- ✅ Pydantic v2 validation
- ✅ Type hints (PEP 484)
- ✅ Async/await patterns
- ✅ Logging (structured)
```

### Стиль кода

```bash
# Форматирование (Black)
black services/

# Linting (Ruff)
ruff check services/

# Type checking (Pyright)
pyright services/
```

### Создание новой фичи

1. Создать branch: `git checkout -b feature/your-feature`
2. Написать код с type hints
3. Написать unit tests (coverage >= 80%)
4. Запустить linter/formatter: `black . && ruff check .`
5. Создать PR с описанием
6. Получить 2+ approvals
7. Merge в main

## 🧪 Тестирование

```bash
# Unit tests
pytest services/ads-integrations/tests/

# Coverage report
pytest --cov=services/ --cov-report=html

# Integration tests
pytest tests/integration/

# Load testing (k6)
k6 run tests/load/ads_integration.js
```

## 🚢 Развёртывание

### Docker Compose (Local/Dev)

```bash
docker compose up -d
docker compose logs -f ads-integrations
```

### Kubernetes (Production)

```bash
kubectl apply -f infra/k8s/ads-integrations/
kubectl apply -f infra/k8s/ml-attribution/
kubectl apply -f infra/k8s/ai-assistant/
```

### Helm (Recommended)

```bash
helm repo add attribly https://charts.attribly.io
helm install ads-ai attribly/ads-ai \
  --namespace production \
  -f infra/helm/values-prod.yaml
```

## 📊 Мониторинг

### Prometheus метрики

```
# Ads Integration
ads_api_calls_total{provider="yandex_direct"}
ads_sync_duration_seconds{provider="vk_ads"}

# ML Attribution
attribution_predictions_total{marketplace="wildberries"}
model_retraining_duration_seconds

# AI Assistant
ai_queries_total{model="gpt-4o"}
ai_tokens_used_total{tier="business"}
```

### Grafana дашборды

- `/grafana/dashboards/ads-integrations.json`
- `/grafana/dashboards/ml-attribution.json`
- `/grafana/dashboards/ai-assistant.json`

## 🔐 Безопасность

- ✅ AES-256-GCM шифрование для OAuth-токенов
- ✅ JWT-аутентификация на всех endpoint'ах
- ✅ Rate limiting по IP и пользователю
- ✅ CORS настройки
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (Pydantic validation)
- ✅ CSRF tokens для form-based requests

## 🛣️ Roadmap

### MVP (Неделя 1-11)
- ✅ Яндекс.Директ интеграция
- ✅ VK Ads интеграция
- ✅ ML-модель атрибуции WB
- ✅ Telegram Ads (базовая)
- ✅ AI-ассистент
- ✅ CSV-экспорт

### Phase 2 (Неделя 12+)
- VK Blogger полная интеграция
- Amazon атрибуция
- Power BI / Tableau коннекторы
- ODBC/JDBC доступ к ClickHouse
- Auto-bidding стратегии

## 📖 Документация

| Документ | Описание |
| :--- | :--- |
| [SPEC_v1.0.md](SPEC_v1.0.md) | Полное техническое задание |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Архитектура, Data Flows, DB Schema |
| [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) | План разработки по фазам |

## 🤝 Contributing

Прежде чем начать разработку, прочитайте:
1. [ARCHITECTURE.md](ARCHITECTURE.md) — понимание архитектуры
2. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) — текущий план
3. Code style guide в wiki

## ❓ FAQ

**Q: С чего начать разработку?**  
A: Начните с Фазы 1 (неделя 1). Начните с настройки инфраструктуры (Docker, миграции, OAuth-фреймворк).

**Q: Какие платформы приоритизированы?**  
A: P0 — Яндекс.Директ и VK Ads. P1 — Telegram Ads и AI-ассистент. P2 — VK Blogger.

**Q: Где находится ML-модель?**  
A: В `services/ml-attribution/ml/` (в разработке). Использует CatBoost + ONNX для inference.

**Q: Как интегрировать OpenAI?**  
A: В `services/ai-assistant/openai_proxy.py`. Используйте API-ключ из `.env`.

**Q: Что такое look-alike аудитории?**  
A: Новые аудитории в рекламных платформах на базе seed-сегментов Attribly (например, VIP клиенты).

## 📞 Контакты

- **Tech Lead:** nikita@attribly.io
- **Product Manager:** product@attribly.io
- **DevOps:** devops@attribly.io
- **Data Science:** ml@attribly.io

---

**Последнее обновление:** 6 мая 2026 г.  
**Статус:** Phase 0 (Planning) → Phase 1 (Начинаем на неделе 1)
