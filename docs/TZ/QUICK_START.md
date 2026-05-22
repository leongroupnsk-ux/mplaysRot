# 🚀 Quick Start Guide для Фазы 1

Быстрый старт для начала разработки модуля Ads + AI.

## ⏱️ Время: ~30 минут

---

## 1️⃣ Клонировать/обновить репозиторий

```bash
cd ~/Desktop/клон\ mplays/
git pull origin main
```

## 2️⃣ Запустить базы данных

```bash
export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH

# Запустить PostgreSQL, ClickHouse, Redis, Kafka
docker compose up -d postgres clickhouse redis kafka zookeeper

# Проверить статус
docker compose ps
```

**Ожидаемый результат:**
```
postgres         ✓ Healthy
clickhouse       ✓ Running
redis            ✓ Running
kafka            ✓ Running
zookeeper        ✓ Running
```

## 3️⃣ Установить зависимости

```bash
# Ads Integration Service
cd services/ads-integrations
pip install -r requirements.txt

# ML Attribution Service (отдельный терминал)
cd services/ml-attribution
pip install -r requirements.txt

# AI Assistant Service (отдельный терминал)
cd services/ai-assistant
pip install -r requirements.txt
```

## 4️⃣ Применить миграции БД

```bash
cd services/api-gateway
alembic upgrade head
```

**Output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_init_postgres, init_postgres
INFO  [alembic.runtime.migration] Running upgrade 001_init_postgres -> 002_add_utm_trax_id
...
INFO  [alembic.runtime.migration] Running upgrade 003_anomaly_log_enrich -> 004_add_ads_integrations_schema, add_ads_integrations_schema
```

## 5️⃣ Запустить микросервисы

**Терминал 1: Ads Integration**
```bash
cd services/ads-integrations
python main.py

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8004
```

**Терминал 2: ML Attribution**
```bash
cd services/ml-attribution
python main.py

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8005
```

**Терминал 3: AI Assistant**
```bash
cd services/ai-assistant
python main.py

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8006
```

## 6️⃣ Проверить health endpoints

```bash
# Ads Integration
curl http://localhost:8004/health
# {"status": "healthy", "service": "ads-integrations", "environment": "development"}

# ML Attribution
curl http://localhost:8005/health
# {"status": "healthy", "service": "ml-attribution", "environment": "development"}

# AI Assistant
curl http://localhost:8006/health
# {"status": "healthy", "service": "ai-assistant", "environment": "development"}
```

## 7️⃣ Открыть интерактивную документацию

- 🔗 Ads Integration: http://localhost:8004/docs
- 🔗 ML Attribution: http://localhost:8005/docs
- 🔗 AI Assistant: http://localhost:8006/docs

---

## ✅ Готово!

Все сервисы запущены и готовы к разработке.

### Что дальше?

- 📖 Прочитайте [ARCHITECTURE.md](ARCHITECTURE.md) для понимания архитектуры
- 📋 Следуйте [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) для фаз разработки
- ✅ Используйте [CHECKLIST.md](CHECKLIST.md) для отслеживания прогресса

---

## 🔧 Полезные команды

### Docker

```bash
# Просмотреть логи всех контейнеров
docker compose logs -f

# Просмотреть логи одного контейнера
docker compose logs -f postgres

# Остановить все
docker compose down

# Перезапустить
docker compose restart postgres
```

### Python / FastAPI

```bash
# Перезагрузить сервис (с auto-reload при изменении файлов)
python main.py

# Установить дополнительный пакет
pip install <package_name>

# Запустить тесты
pytest tests/

# Проверить стиль кода
black . && ruff check .
```

### PostgreSQL

```bash
# Подключиться к БД
psql postgresql://attribly:attribly@localhost:5432/attribly

# Список таблиц
\dt

# Просмотреть миграции
SELECT version, description FROM alembic_version;
```

### ClickHouse

```bash
# Подключиться через клиент
clickhouse-client -h localhost

# Просмотреть таблицы
SHOW TABLES;

# Query
SELECT COUNT(*) FROM tracking_events;
```

---

## 🐛 Troubleshooting

### Ошибка: "Address already in use"

```bash
# Найти процесс на порту 8004
lsof -i :8004

# Убить процесс
kill -9 <PID>
```

### Ошибка: PostgreSQL не запускается

```bash
# Проверить логи
docker compose logs postgres

# Удалить том и переинициализировать
docker compose down -v
docker compose up -d postgres
```

### Ошибка: "No such file or directory: 'alembic.ini'"

```bash
# Убедитесь, что вы в правильной директории
cd services/api-gateway
alembic upgrade head
```

### Ошибка: Python модули не найдены

```bash
# Убедитесь, что виртуальное окружение активировано
which python

# Если нет, создайте или активируйте
python -m venv venv
source venv/bin/activate  # macOS/Linux
# или
venv\Scripts\activate  # Windows
```

---

## 📊 Проверка БД

```sql
-- PostgreSQL: новые таблицы
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Должны быть:
-- - integrations
-- - ad_campaigns
-- - ad_performance
-- - lookalike_audiences
-- - ml_models
-- - ai_queries
-- - attributed_orders
```

---

## 🎯 Контрольный список для Фазы 1

- [ ] Docker контейнеры запущены и здоровы
- [ ] Миграции БД применены успешно
- [ ] Все 3 микросервиса запущены на портах 8004-8006
- [ ] Health endpoints возвращают 200
- [ ] Интерактивная документация доступна (/docs)
- [ ] Новые таблицы видны в PostgreSQL
- [ ] Можно создавать простые запросы к API

---

## 🚀 Next Steps

1. Прочитайте архитектуру: [ARCHITECTURE.md](ARCHITECTURE.md)
2. Выберите свою фазу разработки: [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
3. Используйте чек-лист: [CHECKLIST.md](CHECKLIST.md)
4. Начните разработку вашего компонента!

---

**Happy coding! 🎉**

По вопросам обращайтесь в Slack: #attribly-ads-ai
