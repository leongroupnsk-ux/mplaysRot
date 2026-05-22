# Новые Микросервисы Attribly — Руководство по использованию

## Обзор

Были добавлены три новых микросервиса для расширения функциональности платформы Attribly:

### 1. **Ads Integrations** (порт 8004)
Управление подключениями к внешним платформам объявлений.

**Основные возможности:**
- OAuth-аутентификация для рекламных платформ (Yandex Direct, VK Ads, Telegram Ads, VK Blogger)
- Синхронизация данных о кампаниях и аудиториях
- Управление look-alike сегментами (похожие аудитории)
- Единая аналитика по всем рекламным платформам

**API Endpoints:**
- `GET /health` — проверка здоровья сервиса
- `GET /api/v1/integrations` — список доступных интеграций
- `POST /api/v1/integrations/{provider}/auth` — начало OAuth потока
- `POST /api/v1/audiences/lookalike/create` — создание look-alike аудитории
- `GET /api/v1/analytics/{campaign_id}` — получение аналитики кампании

**Docker:**
```bash
docker exec mplays-ads-integrations-1 curl http://localhost:8004/health
```

---

### 2. **ML Attribution** (порт 8005)
Сервис машинного обучения для атрибуции заказов и конверсий.

**Основные возможности:**
- Машинное обучение для определения источника заказа (какой клик привел к заказу)
- Предсказание вероятности конверсии
- Обучение и переобучение моделей
- Кэширование моделей в Redis
- Поддержка ONNX для быстрого инфиренса

**API Endpoints:**
- `GET /health` — проверка здоровья сервиса
- `POST /api/v1/attribution/predict` — предсказание атрибуции заказа
- `POST /api/v1/attribution/train` — запуск обучения модели
- `GET /api/v1/models` — список доступных моделей

**Модель:**
- Входные признаки: маркетплейс, сумма заказа, геолокация, тип устройства, временной интервал
- Выходные значения: вероятность атрибуции к каждому источнику трафика

**Docker:**
```bash
docker exec mplays-ml-attribution-1 curl http://localhost:8005/health
```

---

### 3. **AI Assistant** (порт 8006)
OpenAI-powered ассистент для рекомендаций и аналитики.

**Основные возможности:**
- Обработка естественного языка с использованием GPT-4
- Ответы на вопросы о логистике и маркетинге
- Рекомендации по оптимизации кампаний
- Интеграция с исторической аналитикой платформы
- Rate limiting по тарифам (Business, Enterprise)

**API Endpoints:**
- `GET /health` — проверка здоровья сервиса
- `POST /api/v1/ai/query` — отправка вопроса ассистенту
- `GET /api/v1/ai/recommendations` — получение рекомендаций

**Контекст:**
ассистент может получать информацию о:
- Статистике склада и запасах
- Продажах и конверсиях
- Статистике объявлений и ROI
- Исторических данных для анализа трендов

**Docker:**
```bash
docker exec mplays-ai-assistant-1 curl http://localhost:8006/health
```

---

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                   Nginx (Port 80/443)                   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────────┐
        │            │            │                 │
   ┌────▼─────┐  ┌──▼─────────┐ ┌▼────────────┐   ┌▼──────────┐
   │ Frontend  │  │ API Gateway│ │ Reporting   │   │ Tracking  │
   │ (3000)    │  │ (8000)     │ │ (8002)      │   │ (8001)    │
   └──────────┘  └──┬──────────┘ └─────────────┘   └───────────┘
                    │
        ┌───────────┼───────────┬──────────────┐
        │           │           │              │
   ┌────▼─────┐  ┌─▼─────────┐┌▼────────────┐┌▼──────────────┐
   │Ads Integ  │  │ML Attrib  ││AI Assistant ││Others (ML,ETL)│
   │(8004)     │  │(8005)     ││ (8006)      ││               │
   └──────────┘  └──────────┘└─────────────┘└────────────────┘
        │           │           │              │
        └───────────┼───────────┼──────────────┘
                    │           │
            ┌───────┴───────────┴───────┐
            │                           │
        ┌───▼────────┐         ┌───────▼──┐
        │ PostgreSQL  │         │ Redis    │
        │ ClickHouse  │         │ Kafka    │
        └─────────────┘         └──────────┘
```

---

## Интеграция с Nginx

Новые сервисы автоматически интегрированы в nginx с следующими маршрутами:

```nginx
# Ads Integrations
/api/ads-integrations/       → http://ads-integrations:8004

# ML Attribution
/api/ml-attribution/         → http://ml-attribution:8005

# AI Assistant
/api/ai/                     → http://ai-assistant:8006
```

---

## Переменные окружения

Добавьте в `.env` файл:

```bash
# AI Assistant (обязательно для работы)
OPENAI_API_KEY=sk-your-api-key-here

# Дополнительные переменные для каждого сервиса автоматически
# загружаются из .env файла в приложении
```

---

## Проверка статуса

```bash
# Проверить все сервисы
docker ps | grep -E "ads-integrations|ml-attribution|ai-assistant"

# Проверить логи
docker logs mplays-ads-integrations-1
docker logs mplays-ml-attribution-1
docker logs mplays-ai-assistant-1

# Проверить health endpoints
curl http://localhost:8004/health
curl http://localhost:8005/health
curl http://localhost:8006/health
```

---

## Базы данных и хранилище

- **PostgreSQL**: используется для хранения конфигурации интеграций и истории запросов ассистента
- **Redis**: кэширование моделей ML и хранение сессий AI ассистента
- **Kafka**: потоковая обработка событий для всех трех сервисов
- **ClickHouse**: хранение аналитики и исторических данных

---

## Развертывание

### Локально
```bash
cd "/Users/nikitaosepkov/Desktop/клон mplays"
docker compose up -d ads-integrations ml-attribution ai-assistant
```

### В полном стеке
```bash
docker compose up -d
```

### Пересборка образов
```bash
docker compose build ads-integrations ml-attribution ai-assistant
```

---

## Документация API

### Docs endpoints
- Ads Integrations: http://localhost:8004/docs
- ML Attribution: http://localhost:8005/docs  
- AI Assistant: http://localhost:8006/docs

Каждый сервис предоставляет интерактивную документацию Swagger UI.

---

## Масштабирование

Сервисы легко масштабируются горизонтально благодаря:
- Микросервисной архитектуре
- Использованию Redis для кэширования
- Поддержке Kafka для асинхронной обработки
- Prometheus метриками для мониторинга

---

## Мониторинг

Все три сервиса экспортируют метрики Prometheus на `/metrics`:

```bash
curl http://localhost:8004/metrics
curl http://localhost:8005/metrics
curl http://localhost:8006/metrics
```

Метрики включают:
- HTTP request duration
- Request count по эндпоинтам
- Error rates
- Latency

---

## Решение проблем

### Сервис не запускается
```bash
# Проверить логи
docker logs mplays-service-name-1

# Проверить requirements
docker exec mplays-service-name-1 pip list | grep fastapi
```

### Port уже занят
```bash
# Найти процесс который использует port
lsof -i :8004
lsof -i :8005
lsof -i :8006

# Убить процесс если нужно
kill -9 <PID>
```

### Ошибка подключения к базе
```bash
# Проверить если postgres здоров
docker ps | grep postgres

# Проверить если redis доступен
docker exec mplays-redis-1 redis-cli ping
```

---

## Примеры использования

### Ads Integrations
```bash
# Получить список интеграций
curl http://localhost:8004/api/v1/integrations

# Начать OAuth для Yandex Direct
curl -X POST http://localhost:8004/api/v1/integrations/yandex_direct/auth \
  -H "Content-Type: application/json" \
  -d '{"redirect_uri": "http://localhost:3000/auth/callback"}'
```

### ML Attribution
```bash
# Предсказать атрибуцию заказа
curl -X POST http://localhost:8005/api/v1/attribution/predict \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "123456",
    "marketplace": "wildberries",
    "order_timestamp": "2024-01-20T10:30:00Z",
    "order_amount": 5000.00,
    "geo": "RU",
    "device_type": "mobile"
  }'
```

### AI Assistant
```bash
# Задать вопрос ассистенту
curl -X POST http://localhost:8006/api/v1/ai/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What campaigns have the highest ROI?",
    "context": {
      "time_period": "last_30_days",
      "marketplace": "all"
    }
  }'
```

---

**Статус**: ✅ Все три микросервиса запущены и работают в полном режиме.
