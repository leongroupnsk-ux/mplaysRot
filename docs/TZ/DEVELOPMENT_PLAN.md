# План разработки модуля Атрибли Ads + AI

## Обзор по фазам

Разработка разделена на 5 фаз с чёткими вехами и приоритетами.

---

## Фаза 1: Подготовка инфраструктуры (Неделя 1)

**Цель:** Подготовить базовую инфраструктуру для всех сервисов

### Задачи:

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 1.1 | Создать структуру микросервисов | P0 | ⏳ To Do | Tech Lead |
| 1.2 | Применить миграции БД (ads_integrations schema) | P0 | ⏳ To Do | Backend |
| 1.3 | Настроить OAuth-фреймворк и Security utilities | P0 | ⏳ To Do | Backend |
| 1.4 | Создать базовые модели SQLAlchemy | P0 | ⏳ To Do | Backend |
| 1.5 | Написать unit-тесты для моделей | P1 | ⏳ To Do | QA |
| 1.6 | Настроить Docker для новых сервисов | P0 | ⏳ To Do | DevOps |
| 1.7 | Подготовить CI/CD пайплайн | P1 | ⏳ To Do | DevOps |

**Deliverables:**
- ✅ Структура директорий `ads-integrations`, `ml-attribution`, `ai-assistant`
- ✅ Docker compose конфиги для 3 новых сервисов
- ✅ Миграции БД (таблицы integrations, ad_campaigns, ad_performance, etc.)
- ✅ Базовые модели ORM
- ✅ OAuth utilities и encryption helpers
- ✅ Health check endpoints на всех сервисах

---

## Фаза 2: Интеграция Яндекс.Директ (Неделя 2-3)

**Цель:** Первая рабочая интеграция с рекламной платформой

### Задачи:

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 2.1 | Реализовать OAuth-flow для Яндекс.Директ | P0 | ⏳ To Do | Backend |
| 2.2 | Создать adapter для Yandex Direct API v5 | P0 | ⏳ To Do | Backend |
| 2.3 | Реализовать сбор статистики (reports endpoint) | P0 | ⏳ To Do | Backend |
| 2.4 | Реализовать загрузку в ad_performance таблицу | P0 | ⏳ To Do | Backend |
| 2.5 | Создать Celery task для ежедневной синхронизации | P0 | ⏳ To Do | Backend |
| 2.6 | Реализовать управление аудиториями (look-alike) | P1 | ⏳ To Do | Backend |
| 2.7 | Написать интеграционные тесты | P0 | ⏳ To Do | QA |
| 2.8 | Создать админ-интерфейс для тестирования | P1 | ⏳ To Do | Frontend |

**API Endpoints:**
```
POST   /api/v1/integrations/yandex_direct/auth
GET    /api/v1/integrations/yandex_direct/status
POST   /api/v1/integrations/yandex_direct/sync
POST   /api/v1/audiences/lookalike/create (yandex_direct)
GET    /api/v1/analytics/performance (фильтр по provider)
```

**Deliverables:**
- ✅ Рабочий OAuth callback для Яндекс.Директ
- ✅ Ежедневная синхронизация статистики
- ✅ UI для подключения кабинета
- ✅ Дашборд с метриками Яндекс.Директ

---

## Фаза 3: Интеграция VK Ads (Неделя 4-5)

**Цель:** Вторая платформа, паттерны развиваются

### Задачи:

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 3.1 | Реализовать OAuth-flow для VK Ads | P0 | ⏳ To Do | Backend |
| 3.2 | Создать adapter для VK Ads API | P0 | ⏳ To Do | Backend |
| 3.3 | Сбор статистики (statistics endpoint) | P0 | ⏳ To Do | Backend |
| 3.4 | Сбор демографических данных | P1 | ⏳ To Do | Backend |
| 3.5 | Синхронизация товарных фидов (CSV/XML) | P1 | ⏳ To Do | Backend |
| 3.6 | Управление аудиториями VK Ads | P1 | ⏳ To Do | Backend |
| 3.7 | Интеграционные тесты | P0 | ⏳ To Do | QA |
| 3.8 | UI для VK Ads кабинета | P1 | ⏳ To Do | Frontend |

**API Endpoints:**
```
POST   /api/v1/integrations/vk_ads/auth
GET    /api/v1/integrations/vk_ads/status
POST   /api/v1/integrations/vk_ads/sync
POST   /api/v1/audiences/lookalike/create (vk_ads)
GET    /api/v1/analytics/performance?provider=vk_ads
```

**Deliverables:**
- ✅ Подключение VK Ads кабинетов
- ✅ Синхронизация статистики с разбором по демографии
- ✅ Единый UI для обоих кабинетов
- ✅ Unified Analytics dashboard

---

## Фаза 4: ML-модель атрибуции WB (Неделя 6-8)

**Цель:** Вероятностная атрибуция заказов Wildberries

### Задачи:

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 4.1 | Подготовить датасет для обучения (historical data) | P0 | ⏳ To Do | Data Scientist |
| 4.2 | Feature engineering (time_diff, geo_match, etc.) | P0 | ⏳ To Do | Data Scientist |
| 4.3 | Обучить CatBoost модель | P0 | ⏳ To Do | Data Scientist |
| 4.4 | Конвертировать в ONNX формат | P0 | ⏳ To Do | Data Scientist |
| 4.5 | Реализовать inference endpoint | P0 | ⏳ To Do | Backend |
| 4.6 | Реализовать batch prediction для исторических заказов | P0 | ⏳ To Do | Backend |
| 4.7 | Webhook для новых заказов WB (real-time) | P0 | ⏳ To Do | Backend |
| 4.8 | User feedback collection (verify/reject) | P1 | ⏳ To Do | Frontend |
| 4.9 | Запланировать ежедневное переобучение (Celery) | P1 | ⏳ To Do | Backend |
| 4.10 | Написать ML-тесты (model validation) | P0 | ⏳ To Do | QA |

**Model Hyperparameters:**
```python
CatBoostClassifier(
    iterations=500,
    learning_rate=0.03,
    depth=6,
    eval_metric='AUC',
    random_state=42,
)
```

**API Endpoints:**
```
POST   /api/v1/attribution/predict
POST   /api/v1/attribution/batch/predict
POST   /api/v1/attribution/verify
GET    /api/v1/models/status?marketplace=wildberries
POST   /api/v1/models/retrain
GET    /api/v1/models/features
```

**Deliverables:**
- ✅ Обученная CatBoost модель (ONNX)
- ✅ Real-time inference сервис
- ✅ Batch attribution для исторических заказов
- ✅ UI для верификации атрибуции
- ✅ Feature importance visualization

---

## Фаза 5: AI-ассистент + Telegram + VK Blogger (Неделя 9-11)

**Цель:** Завершить базовый функционал

### 5.1 AI Assistant (P1, 2 недели)

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 5.1.1 | Реализовать context builder (warehouse, sales, ads) | P1 | ⏳ To Do | Backend |
| 5.1.2 | Создать OpenAI proxy с rate limiting | P1 | ⏳ To Do | Backend |
| 5.1.3 | Реализовать Redis кеширование ответов | P1 | ⏳ To Do | Backend |
| 5.1.4 | Логирование для аудита (ai_queries таблица) | P1 | ⏳ To Do | Backend |
| 5.1.5 | Тарификация по tier (Business 50/мес, Enterprise безлимит) | P1 | ⏳ To Do | Backend |
| 5.1.6 | UI интеграция (right panel в дашборде) | P1 | ⏳ To Do | Frontend |
| 5.1.7 | Тесты (mock OpenAI API) | P0 | ⏳ To Do | QA |

**API Endpoints:**
```
POST   /api/v1/ai/ask
GET    /api/v1/ai/history
GET    /api/v1/ai/usage
```

### 5.2 Telegram Ads (P1, 2 недели)

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 5.2.1 | Реализовать Telegram Ads Platform API adapter | P1 | ⏳ To Do | Backend |
| 5.2.2 | Pixel tracking integration | P1 | ⏳ To Do | Backend |
| 5.2.3 | Event collection (click, add_to_cart, purchase) | P1 | ⏳ To Do | Backend |
| 5.2.4 | Интеграционные тесты | P1 | ⏳ To Do | QA |

### 5.3 VK Blogger (P2, 3 недели)

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 5.3.1 | Реализовать VK Blogger API adapter | P2 | ⏳ To Do | Backend |
| 5.3.2 | Сбор метрик публикаций (reach, engagement) | P2 | ⏳ To Do | Backend |
| 5.3.3 | Оценка эффективности блогера по доходу | P2 | ⏳ To Do | Backend |

**Deliverables:**
- ✅ AI Assistant с контекстом (warehouse, sales, ads)
- ✅ Telegram Ads статистика
- ✅ VK Blogger интеграция
- ✅ Unified Analytics Dashboard

---

## Фаза 6: Экспорт и BI-интеграции (Неделя 12-13) [Roadmap Phase 2]

| ID | Задача | Приоритет | Статус | Ответственный |
| :--- | :--- | :---: | :---: | :--- |
| 6.1 | Реализовать CSV-экспорт для атрибуции | P1 | ⏳ To Do | Backend |
| 6.2 | Экспорт логистических данных | P1 | ⏳ To Do | Backend |
| 6.3 | Celery background task для больших экспортов | P1 | ⏳ To Do | Backend |
| 6.4 | Email уведомления о готовности файла | P1 | ⏳ To Do | Backend |
| 6.5 | Power BI коннектор (будущее) | P3 | ⏳ To Do | Backend |
| 6.6 | Tableau коннектор (будущее) | P3 | ⏳ To Do | Backend |

---

## Метрики успеха по фазам

| Фаза | Метрика | Целевое значение |
| :--- | :--- | :---: |
| 1 | Развёртывание всех 3 микросервисов | 100% |
| 2 | Сбор статистики Яндекс.Директ | 100% accuracy |
| 3 | Поддержка 2 платформ | 100% data sync |
| 4 | ML-модель готова | AUC > 0.85 |
| 5 | AI-ассистент работает | Latency < 2s (с кешем) |
| 6 | CSV-экспорт доступен | <10s для 100K строк |

---

## Риски и mitigation

| Риск | Влияние | Вероятность | Mitigation |
| :--- | :--- | :---: | :--- |
| API лимиты Яндекс.Директ | Высокое | Средняя | Кеширование, batch requests |
| ML-модель переобучается | Средн. | Средняя | Валидация на test set, мониторинг accuracy |
| OpenAI API downtime | Высокое | Низкая | Graceful degradation, fallback responses |
| OAuth-токены истекают | Средн. | Высокая | Автоматическое обновление refresh tokens |
| ClickHouse query производительность | Средн. | Средняя | Индексирование, партиционирование |

---

## Stakeholder коммуникация

**Weekly:**
- Tech Lead → Product Manager: статус выполнения, blockers
- Backend → QA: готовые features для тестирования

**Bi-weekly:**
- All teams: Demo completed features
- Product → Users: Early access программа

**Monthly:**
- Steering committee: Roadmap review, resource allocation

---

## Definition of Done

Для каждой фазы задача считается Done, когда:

- ✅ Code написан и reviewed (2+ approvals)
- ✅ Unit tests покрытие >= 80%
- ✅ Integration tests passed
- ✅ Documentation обновлена
- ✅ Security review пройден
- ✅ Performance тесты в норме (latency, memory)
- ✅ Deployed в staging
- ✅ Product Manager sign-off

---

## Timeline в виде Gantt

```
Фаза 1: [=======]           (Неделя 1)
Фаза 2: [==========]         (Неделя 2-3)
Фаза 3:           [==========] (Неделя 4-5)
Фаза 4:                   [============] (Неделя 6-8)
Фаза 5:                           [==========] (Неделя 9-11)
Фаза 6:                                      [===] (Неделя 12-13)

MVP готов: ════════════════════════════════════ (Неделя 11)
```

---

## Next Steps

1. ✅ Одобрить план разработки
2. ⏳ Выделить resources (backend, frontend, data scientist, devops)
3. ⏳ Создать Jira эпики для каждой фазы
4. ⏳ Начать Фазу 1 (Неделя 1)
5. ⏳ Настроить daily standups
