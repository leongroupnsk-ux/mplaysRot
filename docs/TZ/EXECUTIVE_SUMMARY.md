# 📋 Executive Summary: Модуль Ads + AI для Attribly

**Дата:** 6 мая 2026 г.  
**Статус:** ✅ Phase 0 (Planning) готова, переход на Phase 1  
**Версия:** 1.0

---

## 🎯 What's Happening?

Запускаем **полный модуль интеграции рекламных кабинетов и AI** в платформу Attribly.

### Для кого это важно?

- **Селлеры:** Единый центр управления рекламой из всех платформ + AI-помощник
- **Product:** Ключевое конкурентное преимущество
- **Tech:** Масштабируемая архитектура, ML + AI интеграция
- **Business:** Увеличение стоимости платформы, более высокие тарифы

---

## ✨ Что включено?

| Компонент | Описание | ETA |
| :--- | :--- | :---: |
| 🔗 **Яндекс.Директ** | OAuth, статистика, аудитории | Нед 2-3 |
| 🔗 **VK Ads** | OAuth, статистика, демография, фиды | Нед 4-5 |
| 🤖 **ML Attribution** | CatBoost модель для WB заказов | Нед 6-8 |
| 💬 **Telegram Ads** | Пиксель-трекинг, базовая статистика | Нед 9-11 |
| 🧠 **AI Assistant** | OpenAI-powered рекомендации | Нед 9-11 |
| 👤 **VK Blogger** | Метрики публикаций | Нед 9-11 |
| 📤 **CSV Export** | Выгрузка для BI-систем | Нед 12-13 |

---

## 🏗️ Архитектура: 3 микросервиса

```
┌─────────────────────────────────────────────┐
│         Frontend (React)                    │
│       http://localhost:3000                 │
└────────────┬─────────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼──┐  ┌─▼──┐  ┌──▼─────────┐
│ API  │  │Auth│  │ Ads Service │
│Gate  │  │    │  │    :8004    │
│:8000 │  │    │  └─────────────┘
└──────┘  └────┘
              │
    ┌─────────┼──────────┐
    │         │          │
┌───▼──────┐ ┌▼───────┐ ┌▼──────────┐
│PostgreSQL│ │ClickHouse│ │   Redis  │
└──────────┘ └────────┘ └──────────┘

┌──────────────────────┐  ┌──────────────────┐
│ ML Attribution Svc   │  │ AI Assistant Svc │
│     :8005            │  │     :8006        │
└──────────────────────┘  └──────────────────┘
```

---

## 📊 Что готово сейчас? (Phase 0 Complete ✅)

### Документация
- ✅ **SPEC_v1.0.md** — 500+ строк техзадания
- ✅ **ARCHITECTURE.md** — подробная архитектура + Data Flows
- ✅ **DEVELOPMENT_PLAN.md** — 6 фаз по 2-4 недели каждая
- ✅ **CHECKLIST.md** — actionable items для каждой фазы
- ✅ **QUICK_START.md** — старт за 30 минут
- ✅ **PROJECT_STRUCTURE.md** — полная карта файлов

### Код (Boilerplate)
- ✅ 3 микросервиса со своими FastAPI приложениями
- ✅ Базовые роутеры (routers/) и конфиги (config.py)
- ✅ Requirements.txt для каждого сервиса
- ✅ Health endpoints

### БД
- ✅ Миграция Alembic с 7 новыми таблицами:
  - integrations (OAuth-токены)
  - ad_campaigns, ad_performance (статистика)
  - lookalike_audiences
  - ml_models, attributed_orders
  - ai_queries (логирование)

---

## 🚀 Что дальше? (Phase 1)

**Неделя 1:** Infrastructure setup
- Установить зависимости
- Применить миграции БД
- Написать OAuth utilities
- Настроить Docker
- Первые unit-тесты

**Результат:** Все 3 сервиса запущены и здоровы ✅

---

## 💰 ROI Калькуляция

### Инвестиция:
- 13 недель разработки (3 backend, 2 frontend, 1 data scientist, 1 devops)
- ~1050 часов = ~$52,500 (при $50/час)

### Возврат:
- **Tier upgrade:** Business $300/мес → $500/мес (+$200/мес)
- **Новые клиенты:** +30% привлечение благодаря feature
- **Сокращение чёрна:** -2 часа в день на рутинные операции

**Breakeven:** 3-4 месяца  
**Profit в Year 1:** $60K+

---

## 🎓 Для каждой роли: Что нужно знать?

### 👨‍💼 Product Manager
- Смотрите [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md) — там графики и метрики
- Следите за Phase gates (конец каждой недели = дели)
- Общайтесь с селлерами о интеграциях (какой приоритет?)

### 👨‍💻 Backend Developer
- Начните с [QUICK_START.md](docs/TZ/QUICK_START.md) — запустить локально
- Выберите вашу фазу в [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md)
- Следуйте [CHECKLIST.md](docs/TZ/CHECKLIST.md) для вашей фазы

### 🎨 Frontend Developer
- Phase 2-3: Создайте UI для подключения кабинетов + дашборд
- Phase 5: AI Assistant интеграция (right panel)
- Phase 6: Export buttons

### 🤖 Data Scientist
- Phase 4: Обучение CatBoost модели (feature engineering, гиперпараметры)
- Phase 5: AI контекст builder (интеграция с OpenAI)

### 🔧 DevOps
- Phase 1: Docker + K8s configs
- Ongoing: Мониторинг + alerting

---

## ⚠️ Риски и mitigation

| Риск | Вероятность | Решение |
| :--- | :---: | :--- |
| API лимиты платформ | 🟡 Средн. | Кеширование + batch requests |
| Delays в интеграциях | 🟡 Средн. | Buffer week + fail-over |
| ML модель переобучается | 🟡 Средн. | Валидация на test set |
| OpenAI downtime | 🔴 Высок. | Graceful degradation |

---

## 📅 Timeline

```
Неделя 1-2:   Phase 0 → Phase 1  (Infrastructure)
Неделя 2-3:   Phase 2 (Yandex Direct)
Неделя 4-5:   Phase 3 (VK Ads)
Неделя 6-8:   Phase 4 (ML Attribution)
Неделя 9-11:  Phase 5 (AI + Telegram + Blogger)
Неделя 12-13: Phase 6 (Export/BI)

✅ MVP: Конец недели 11 (3 месяца)
```

---

## 📚 Документы для каждой аудитории

### Для техлида
- Прочитайте: [SPEC_v1.0.md](docs/TZ/SPEC_v1.0.md) + [ARCHITECTURE.md](docs/TZ/ARCHITECTURE.md)
- Используйте: [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md) для планирования спринтов
- Следите: [CHECKLIST.md](docs/TZ/CHECKLIST.md) для прогресса

### Для Product Manager
- Главное: [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md) — там timeline и метрики
- Фон: [SPEC_v1.0.md](docs/TZ/SPEC_v1.0.md) для обсуждений с клиентами

### Для Backend Developer
- Start: [QUICK_START.md](docs/TZ/QUICK_START.md)
- Work: [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md) для своей фазы
- Reference: [ARCHITECTURE.md](docs/TZ/ARCHITECTURE.md) для понимания data flows
- Track: [PROJECT_STRUCTURE.md](docs/TZ/PROJECT_STRUCTURE.md) для файлов

### Для Frontend Developer
- Overview: [README.md](docs/TZ/README.md)
- Tech details: [ARCHITECTURE.md](docs/TZ/ARCHITECTURE.md) (API contracts)
- Tasks: [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md) Phase 2-6

### Для QA Engineer
- Check: [DEVELOPMENT_PLAN.md](docs/TZ/DEVELOPMENT_PLAN.md) — что нужно тестировать
- Reference: [CHECKLIST.md](docs/TZ/CHECKLIST.md) — Definition of Done

---

## 🎯 Next Actions (Immediate)

### Today (День запуска)
- [ ] **Tech Lead** прочитает SPEC + ARCHITECTURE
- [ ] **Product Manager** прочитает DEVELOPMENT_PLAN
- [ ] **Team Lead** проведёт kick-off meeting (30 мин)

### This Week (Неделя 1)
- [ ] **Backend** запускает Phase 1 по [QUICK_START.md](docs/TZ/QUICK_START.md)
- [ ] **DevOps** настраивает Docker + K8s
- [ ] **All** используют [CHECKLIST.md](docs/TZ/CHECKLIST.md)

### Ongoing
- [ ] **Daily standups:** 15 мин (blockers, progress)
- [ ] **Weekly demos:** пятница 4 PM UTC
- [ ] **Weekly planning:** понедельник 10 AM UTC

---

## 💬 Communication Channels

- **Slack:** #attribly-ads-ai
- **GitHub:** attribly/attribly-ads-ai (если отдельный репо)
- **Docs:** `/docs/TZ/` в этом репо

---

## ✅ Success Criteria

MVP (конец недели 11):
- ✅ Яндекс.Директ + VK Ads статистика работает
- ✅ ML модель обучена (AUC > 0.85)
- ✅ AI Assistant отвечает на вопросы
- ✅ Telegram Ads базовая интеграция
- ✅ Система монетизирована (Business/Enterprise тиры)

---

## 📞 Key Contacts

| Role | Name | Contact |
| :--- | :--- | :--- |
| Tech Lead | Никита | nikita@attribly.io |
| Product Manager | [Name] | product@attribly.io |
| Backend Lead | [Name] | backend@attribly.io |
| DevOps | [Name] | devops@attribly.io |
| Data Science | [Name] | ml@attribly.io |

---

## 🏁 Conclusion

**Это большой проект, но он разбит на управляемые фазы.**

Каждая неделя имеет чёткие deliverables и Definition of Done. 

**Началось! 🚀**

---

**Документ подготовлен:** Tech Lead  
**Одобрено:** Product Manager  
**Версия:** 1.0  
**Дата:** 6 мая 2026
