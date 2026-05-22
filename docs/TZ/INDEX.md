# 📑 Index: Документация модуля Ads + AI для Attribly

Полный каталог всей документации. **Начните отсюда!**

---

## 🚀 Быстрый вход (Start Here)

| Кто вы? | Читайте | ⏱️ |
| :--- | :--- | :---: |
| **Менеджер** (нужен overview) | [EXECUTIVE_SUMMARY.md](#executive-summary) | 5 мин |
| **Backend** (начинаю разработку) | [QUICK_START.md](#quick-start) → [DEVELOPMENT_PLAN.md](#development-plan) | 30 мин |
| **Tech Lead** (нужна полная картина) | [SPEC_v1.0.md](#spec) + [ARCHITECTURE.md](#architecture) | 60 мин |
| **QA** (что тестировать?) | [CHECKLIST.md](#checklist) + [DEVELOPMENT_PLAN.md](#development-plan) | 30 мин |
| **DevOps** (инфра) | [ARCHITECTURE.md](#architecture) + [PROJECT_STRUCTURE.md](#project-structure) | 45 мин |

---

## 📖 Все документы

### 📋 [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
**Для:** Менеджеры, Product, C-level  
**Что:** Краткое резюме проекта, ROI, timeline, риски  
**Когда:** Первый документ для ознакомления  
**Размер:** ~400 строк  

**Ключевые точки:**
- ✨ Что включено (3 микросервиса, 6 платформ)
- 💰 ROI: $52K инвестиция → $60K+ profit в year 1
- 📅 Timeline: 13 недель до MVP
- ⚠️ Риски и их решения

---

### 🎯 [SPEC_v1.0.md](SPEC_v1.0.md)
**Для:** Техлиды, архитекторы, все разработчики  
**Что:** Полное техническое задание со всеми требованиями  
**Когда:** После EXECUTIVE_SUMMARY, перед архитектурой  
**Размер:** ~500 строк  

**Разделы:**
1. Общие сведения о модуле
2. Цели и задачи
3. Функциональные требования (по платформам)
   - 3.1 Яндекс.Директ
   - 3.2 VK Ads
   - 3.3 Telegram Ads
   - 3.4 VK Blogger
   - 3.5 AI (OpenAI)
   - 3.6 ML-модель WB
   - 3.7 BI-интеграции
4. Технические требования
5. API-контракты
6. Roadmap с приоритетами

**Используйте для:** Обсуждения с клиентами, дизайн-ревью, scope management

---

### 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md)
**Для:** Все разработчики, особенно backend/devops  
**Что:** Детальная архитектура + потоки данных + схемы БД  
**Когда:** После SPEC, перед началом разработки  
**Размер:** ~600 строк  

**Содержит:**
1. Диаграмма системы (ASCII art)
2. Микросервисная архитектура (3 сервиса)
3. Потоки данных (3 flow-диаграммы)
4. PostgreSQL schema (7 таблиц)
5. ClickHouse schema (быстрая аналитика)
6. Security considerations
7. Docker Compose конфиг
8. Мониторинг + Prometheus метрики

**Используйте для:** Design review, data flow понимание, DB design

---

### 📋 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
**Для:** Все разработчики, scrum-мастер, PM  
**Что:** План по фазам (6 фаз, 13 недель) с actionable tasks  
**Когда:** Используйте каждый день для планирования спринтов  
**Размер:** ~700 строк  

**6 фаз:**
1. **Phase 1 (Неделя 1):** Infrastructure
2. **Phase 2 (Неделя 2-3):** Yandex Direct
3. **Phase 3 (Неделя 4-5):** VK Ads
4. **Phase 4 (Неделя 6-8):** ML Attribution
5. **Phase 5 (Неделя 9-11):** AI + Telegram + Blogger
6. **Phase 6 (Неделя 12-13):** Export/BI

**Каждая фаза содержит:**
- Список задач с приоритетами (P0, P1, P2)
- Ответственные
- API endpoints для реализации
- Deliverables

**Используйте для:** Спринт-планирование, roadmapping, статус-отчёты

---

### ✅ [CHECKLIST.md](CHECKLIST.md)
**Для:** Разработчики, QA, техлид  
**Что:** Детальный чек-лист для каждой фазы (Phase 0 ✅ до Phase 6)  
**Когда:** Ежедневно во время разработки  
**Размер:** ~800 строк  

**Содержит для каждой фазы:**
- Backend задачи
- Frontend задачи
- QA задачи
- DevOps задачи
- Definition of Done

**Используйте для:** Отслеживание прогресса, ежедневные standups

---

### 🚀 [QUICK_START.md](QUICK_START.md)
**Для:** Backend разработчики (новые или вернулись на проект)  
**Что:** Пошаговый старт разработки (30 минут)  
**Когда:** Прямо сейчас, чтобы запустить локально  
**Размер:** ~250 строк  

**Шаги:**
1. Клонировать репо
2. Запустить Docker контейнеры
3. Установить зависимости
4. Применить миграции БД
5. Запустить 3 микросервиса
6. Проверить health endpoints
7. Открыть Swagger docs

**Используйте для:** Onboarding новых разработчиков, локальное тестирование

---

### 📁 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
**Для:** Все разработчики, архитектор  
**Что:** Полная карта структуры проекта (файлы, директории)  
**Когда:** Reference при создании новых файлов  
**Размер:** ~400 строк  

**Содержит:**
1. Full directory tree
2. Файлы по фазам (что готово, что нужно создать)
3. Data flow по структуре
4. Checklist файлов для фазы 1

**Используйте для:** Ориентирование в проекте, поиск файлов

---

### 📘 [README.md](README.md)
**Для:** Всем и каждому  
**Что:** General overview проекта, quick links, FAQ  
**Когда:** Первая точка входа после EXECUTIVE_SUMMARY  
**Размер:** ~300 строк  

**Содержит:**
1. Что это (overview)
2. Ключевые возможности
3. Структура проекта
4. Быстрый старт (link to QUICK_START)
5. Микросервисы (description)
6. API docs
7. Разработка (style guide)
8. Тестирование
9. Deployment
10. Мониторинг
11. Roadmap
12. FAQ

**Используйте для:** Ознакомление с проектом, общие вопросы

---

## 🗺️ Чтение по ролям

### 👨‍💼 Product Manager / Business
```
1. EXECUTIVE_SUMMARY.md          (5 мин)
2. SPEC_v1.0.md (Разделы 2-3)   (15 мин)
3. DEVELOPMENT_PLAN.md (Timeline)(10 мин)

Итого: 30 мин
```

### 👨‍💻 Backend Developer
```
1. README.md                      (5 мин)
2. QUICK_START.md                 (30 мин - практика!)
3. ARCHITECTURE.md                (30 мин)
4. DEVELOPMENT_PLAN.md (ваша фаза)(15 мин)
5. CHECKLIST.md (ваша фаза)       (10 мин)
6. PROJECT_STRUCTURE.md (reference)(-min)

Итого: 90 мин, но QUICK_START нужно реально выполнить!
```

### 🎨 Frontend Developer
```
1. README.md                      (5 мин)
2. ARCHITECTURE.md (API contracts)(15 мин)
3. DEVELOPMENT_PLAN.md (Phase 2-6)(20 мин)
4. QUICK_START.md (понять архи)   (10 мин)

Итого: 50 мин
```

### 🤖 Data Scientist
```
1. SPEC_v1.0.md (Раздел 3.6)     (20 мин)
2. DEVELOPMENT_PLAN.md (Phase 4)  (15 мин)
3. ARCHITECTURE.md (ML Service)   (15 мин)

Итого: 50 мин
```

### 🔧 DevOps / SRE
```
1. ARCHITECTURE.md (Diagram + K8s) (20 мин)
2. PROJECT_STRUCTURE.md            (15 мин)
3. DEVELOPMENT_PLAN.md (Phase 1)   (15 мин)
4. QUICK_START.md (Docker Compose) (20 мин)

Итого: 70 мин
```

### 🧪 QA / Test Engineer
```
1. SPEC_v1.0.md (Раздел 3)         (30 мин)
2. DEVELOPMENT_PLAN.md (все фазы)  (30 мин)
3. CHECKLIST.md (Definition of Done)(20 мин)

Итого: 80 мин
```

---

## 🎯 Документы по фазам

### Phase 0: Planning (✅ COMPLETE)
- ✅ SPEC_v1.0.md
- ✅ ARCHITECTURE.md
- ✅ DEVELOPMENT_PLAN.md
- ✅ Все остальные документы

### Phase 1: Infrastructure (Неделя 1)
- 📖 Используй: QUICK_START.md, CHECKLIST.md (Phase 1)
- 📖 Reference: ARCHITECTURE.md, PROJECT_STRUCTURE.md

### Phase 2-3: Yandex Direct + VK Ads (Неделя 2-5)
- 📖 Используй: DEVELOPMENT_PLAN.md (Phase 2-3), CHECKLIST.md
- 📖 Reference: SPEC_v1.0.md (Раздел 3.1-3.2), ARCHITECTURE.md

### Phase 4: ML Attribution (Неделя 6-8)
- 📖 Используй: DEVELOPMENT_PLAN.md (Phase 4), CHECKLIST.md
- 📖 Reference: SPEC_v1.0.md (Раздел 3.6), ARCHITECTURE.md

### Phase 5: AI + More (Неделя 9-11)
- 📖 Используй: DEVELOPMENT_PLAN.md (Phase 5), CHECKLIST.md
- 📖 Reference: SPEC_v1.0.md (Раздел 3.5)

### Phase 6: Export/BI (Неделя 12-13)
- 📖 Используй: DEVELOPMENT_PLAN.md (Phase 6), CHECKLIST.md
- 📖 Reference: SPEC_v1.0.md (Раздел 3.7)

---

## 🔍 Как найти информацию?

| Вопрос | Ответ в документе |
| :--- | :--- |
| Что такое этот проект? | README.md или EXECUTIVE_SUMMARY.md |
| Какие требования? | SPEC_v1.0.md (Раздел 3) |
| Как устроена система? | ARCHITECTURE.md |
| Что мне нужно делать? | DEVELOPMENT_PLAN.md (ваша фаза) |
| Как проверить, что я готов? | CHECKLIST.md (ваша фаза) |
| Как запустить локально? | QUICK_START.md |
| Где находится файл X? | PROJECT_STRUCTURE.md |
| Какой timeline? | DEVELOPMENT_PLAN.md (Timeline table) |
| Какие риски? | EXECUTIVE_SUMMARY.md |
| Как авторизоваться в Яндекс.Директ? | SPEC_v1.0.md (3.1.1) |
| Какие метрики ML модели? | SPEC_v1.0.md (3.6.2) |
| Как работает AI Assistant? | SPEC_v1.0.md (3.5) + ARCHITECTURE.md |

---

## 📊 Размеры документов

| Документ | Строк | Читать за | Тип |
| :--- | ---: | :---: | :--- |
| EXECUTIVE_SUMMARY.md | ~400 | 5 мин | Overview |
| SPEC_v1.0.md | ~500 | 15 мин | Requirements |
| ARCHITECTURE.md | ~600 | 20 мин | Technical |
| DEVELOPMENT_PLAN.md | ~700 | 25 мин | Planning |
| CHECKLIST.md | ~800 | 20 мин | Tracking |
| QUICK_START.md | ~250 | 30 мин | Tutorial |
| PROJECT_STRUCTURE.md | ~400 | 15 мин | Reference |
| README.md | ~300 | 10 мин | Overview |

**Итого:** ~3,750 строк документации

---

## ✨ Pro Tips

1. **Для новичков:** Начните с README → QUICK_START → ваша фаза в DEVELOPMENT_PLAN
2. **Для параллелизма:** Разные команды читают разные разделы SPEC одновременно
3. **Для reference:** Bookmark PROJECT_STRUCTURE.md для быстрого поиска файлов
4. **Для tracking:** Используйте CHECKLIST.md как source of truth для прогресса
5. **Для meetings:** Показывайте timeline из DEVELOPMENT_PLAN.md

---

## 🔗 Структура ссылок в документах

Все документы **кросс-ссылаются** друг на друга:

```
EXECUTIVE_SUMMARY
    ↓
    ├─→ SPEC_v1.0 (детали)
    ├─→ DEVELOPMENT_PLAN (timeline)
    └─→ CHECKLIST (tracking)

SPEC_v1.0
    ↓
    ├─→ ARCHITECTURE (tech details)
    ├─→ DEVELOPMENT_PLAN (что разрабатывать)
    └─→ CHECKLIST (что тестировать)

ARCHITECTURE
    ↓
    ├─→ PROJECT_STRUCTURE (где файлы)
    ├─→ QUICK_START (как запустить)
    └─→ DEVELOPMENT_PLAN (phases)

DEVELOPMENT_PLAN
    ↓
    ├─→ CHECKLIST (для каждой фазы)
    └─→ SPEC_v1.0 (детали требований)

CHECKLIST
    ↓
    └─→ Каждая фаза ссылает на DEVELOPMENT_PLAN

QUICK_START
    ↓
    └─→ README, ARCHITECTURE (дальше читать)
```

---

## 🎓 Рекомендуемый порядок чтения

### Для новичка в проекте
1. **Day 1:** README.md → EXECUTIVE_SUMMARY.md (1 час)
2. **Day 2:** QUICK_START.md (практика, 1.5 часа)
3. **Day 3:** ARCHITECTURE.md → PROJECT_STRUCTURE.md (1 час)
4. **Day 4:** DEVELOPMENT_PLAN.md + ваша фаза CHECKLIST.md (1 час)

**Итого:** 4 дня на ознакомление

### Для повторного входа
1. **QUICK_START.md** — вспомнить как запустить (10 мин)
2. **DEVELOPMENT_PLAN.md** — увидеть текущую фазу (5 мин)
3. **CHECKLIST.md** — начать работу (5 мин)

**Итого:** 20 мин на вспоминание

---

## 📞 Contacts

- **Questions?** Слайте в #attribly-ads-ai (Slack)
- **Bug in docs?** GitHub Issue
- **General:**  nikita@attribly.io

---

## 📄 Версионирование

| Документ | Версия | Дата |
| :--- | :---: | :--- |
| EXECUTIVE_SUMMARY | 1.0 | 2026-05-06 |
| SPEC_v1.0 | 1.0 | 2026-05-06 |
| ARCHITECTURE | 1.0 | 2026-05-06 |
| DEVELOPMENT_PLAN | 1.0 | 2026-05-06 |
| CHECKLIST | 1.0 | 2026-05-06 |
| QUICK_START | 1.0 | 2026-05-06 |
| PROJECT_STRUCTURE | 1.0 | 2026-05-06 |
| README | 1.0 | 2026-05-06 |
| **INDEX** | **1.0** | **2026-05-06** |

---

## ✅ Next Step

**👉 [Начните с EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) (5 минут)**

или

**👉 [Если вы разработчик — QUICK_START.md](QUICK_START.md) (30 минут)**

---

**Документация готова! Вперёд! 🚀**

_Last updated: 6 мая 2026 г._
