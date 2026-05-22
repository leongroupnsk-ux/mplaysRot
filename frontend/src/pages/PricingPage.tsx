import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { PLANS, ANNUAL_DISCOUNT, LOGISTICS_TRACKER_MONTHLY, LOGISTICS_TRACKER_YEARLY, EXTRA_STORE_PRICE } from "../constants/pricing";
import styles from "./PricingPage.module.css";

// ── FAQ data ──────────────────────────────────────────────────────────────────
const FAQS = [
  {
    q: "Можно ли сменить тариф?",
    a: "Да, в любой момент. При переходе на более высокий тариф оставшиеся дни пересчитываются пропорционально. При переходе на более низкий — изменения вступают со следующего расчётного периода.",
  },
  {
    q: "Как оплатить от юрлица?",
    a: "Выставим счёт и закроющие документы (акт + счёт-фактура) на вашу компанию. Напишите на billing@mplays.ru или через форму Enterprise ниже.",
  },
  {
    q: "Есть ли возврат средств?",
    a: "Да — 14-дневная политика money-back. Если за первые 14 дней платного тарифа вы решите, что MPlays вам не подходит, вернём деньги без вопросов.",
  },
  {
    q: "Можно ли заморозить подписку?",
    a: "Да, на срок до 30 дней. Тариф приостанавливается, доступ сохраняется только к истории данных. Напишите в поддержку — активируем заморозку в течение часа.",
  },
  {
    q: "Что такое Logistics Tracker?",
    a: "Модуль контроля складских остатков и продаж на Wildberries: обзор складов с картой и KPI, детализация по товарам и размерам, заказы и возвраты с аналитикой причин, автоматические рекомендации по пополнению.",
  },
  {
    q: "Что включено в тариф Free?",
    a: "1 магазин WB/Ozon, 1 магазин Яндекс.Маркет, 500 отслеживаемых переходов в месяц, 1 рекламный кабинет (Яндекс.Директ). Базовая аналитика без ML-атрибуции и ИИ-ассистента.",
  },
];

// ── Feature rows for the comparison table ────────────────────────────────────
const FEATURE_ROWS: { label: string; values: string[] }[] = [
  { label: "Цена / мес",                     values: ["0 ₽", "7 190 ₽", "19 190 ₽", "от 47 990 ₽"] },
  { label: "Магазины WB / Ozon",             values: ["1", "2", "10", "∞"] },
  { label: "Магазины Яндекс.Маркет",         values: ["1", "1", "3", "∞"] },
  { label: "Переходов / мес",                values: ["500", "5 000", "50 000", "∞"] },
  { label: "Рекламные кабинеты",             values: ["1 (Директ)", "3", "Все", "Все"] },
  { label: "Сегментация и выгрузка",         values: ["—", "—", "✓", "✓"] },
  { label: "Модель атрибуции WB",            values: ["—", "Базовая", "ML", "ML + верификация"] },
  { label: "Look-alike аудитории",           values: ["—", "—", "✓", "✓ + автоактивация"] },
  { label: "Logistics Tracker",              values: ["—", "—", "Полный", "Полный + ИИ"] },
  { label: "ИИ-ассистент",                   values: ["—", "—", "50 / мес", "∞"] },
  { label: "Поддержка",                      values: ["Email", "Email", "Приоритетная", "Персональный менеджер"] },
  { label: "Интеграция с CRM / BI",          values: ["—", "—", "—", "✓"] },
  { label: "SLA",                            values: ["—", "—", "99.5%", "99.9%"] },
];

export default function PricingPage() {
  const navigate = useNavigate();
  const [yearly, setYearly] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  // Enterprise lead form
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", stores: "" });
  const [formSent, setFormSent] = useState(false);
  const [formLoading, setFormLoading] = useState(false);

  const getPrice = (monthly: number) =>
    yearly ? Math.round(monthly * 12 * (1 - ANNUAL_DISCOUNT)) : monthly;

  const handleEnterpriseSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormLoading(true);
    // In production: POST /api/v1/leads/enterprise
    await new Promise((r) => setTimeout(r, 600));
    setFormSent(true);
    setFormLoading(false);
  };

  return (
    <div className={styles.page}>
      {/* Back link */}
      <button className={styles.back} onClick={() => navigate("/")}>← Главная</button>

      {/* Hero */}
      <header className={styles.hero}>
        <h1 className={styles.heroTitle}>Тарифы MPlays</h1>
        <p className={styles.heroSub}>
          Прозрачные цены без скрытых платежей. Годовая подписка — скидка {Math.round(ANNUAL_DISCOUNT * 100)}%.
        </p>

        {/* Period toggle */}
        <div className={styles.toggle} role="group" aria-label="Период оплаты">
          <button
            className={`${styles.toggleBtn} ${!yearly ? styles.toggleBtnActive : ""}`}
            onClick={() => setYearly(false)}
          >
            Помесячно
          </button>
          <button
            className={`${styles.toggleBtn} ${yearly ? styles.toggleBtnActive : ""}`}
            onClick={() => setYearly(true)}
          >
            Годовая
            <span className={styles.toggleSave}>−{Math.round(ANNUAL_DISCOUNT * 100)}%</span>
          </button>
        </div>
      </header>

      {/* Plan cards */}
      <section className={styles.cardsSection} aria-label="Тарифные планы">
        <div className={styles.cards}>
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`${styles.card} ${plan.highlighted ? styles.cardHighlighted : ""} ${plan.id === "enterprise" ? styles.cardEnterprise : ""}`}
            >
              {plan.badge && <div className={styles.cardBadge}>{plan.badge}</div>}
              <div className={styles.cardName}>{plan.name}</div>
              <div className={styles.cardDesc}>{plan.description}</div>
              <div className={styles.cardPrice}>
                {plan.id === "enterprise" ? (
                  <span className={styles.cardAmount}>{plan.priceLabel}</span>
                ) : (
                  <>
                    <span className={styles.cardAmount}>
                      {plan.price === 0 ? "0 ₽" : `${getPrice(plan.price!).toLocaleString("ru")} ₽`}
                    </span>
                    <span className={styles.cardPeriod}>/{yearly ? "год" : "мес"}</span>
                  </>
                )}
              </div>
              {plan.id !== "enterprise" && yearly && plan.price! > 0 && (
                <div className={styles.cardSaveLabel}>
                  экономия {Math.round(plan.price! * 12 * ANNUAL_DISCOUNT).toLocaleString("ru")} ₽
                </div>
              )}
              <ul className={styles.cardFeatures}>
                {plan.features.map((f) => (
                  <li key={f.label} className={`${styles.cardFeature} ${f.available ? "" : styles.cardFeatureOff}`}>
                    <span aria-hidden>{f.available ? "✓" : "✕"}</span>
                    {f.label}: <strong>{f.value}</strong>
                  </li>
                ))}
              </ul>
              <button
                className={plan.highlighted || plan.id === "enterprise" ? styles.btnPrimary : styles.btnOutline}
                onClick={() =>
                  plan.id === "enterprise"
                    ? document.getElementById("enterprise-form")?.scrollIntoView({ behavior: "smooth" })
                    : navigate("/register")
                }
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Full comparison table */}
      <section className={styles.tableSection} aria-label="Полное сравнение тарифов">
        <h2 className={styles.sectionTitle}>Детальное сравнение</h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.thFeature}>Функция</th>
                {PLANS.map((p) => (
                  <th key={p.id} className={`${styles.th} ${p.highlighted ? styles.thHighlighted : ""}`}>
                    {p.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FEATURE_ROWS.map((row) => (
                <tr key={row.label}>
                  <td className={styles.tdFeature}>{row.label}</td>
                  {row.values.map((v, i) => (
                    <td key={i} className={`${styles.td} ${PLANS[i]?.highlighted ? styles.tdHighlighted : ""}`}>
                      {v === "✓" ? <span className={styles.check}>✓</span>
                       : v === "—" ? <span className={styles.dash}>—</span>
                       : v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Add-ons */}
      <section className={styles.addonsSection} aria-label="Дополнительные опции">
        <h2 className={styles.sectionTitle}>Дополнительные опции</h2>
        <div className={styles.addons}>
          {[
            {
              name: "Logistics Tracker (отдельный модуль)",
              price: `${LOGISTICS_TRACKER_MONTHLY.toLocaleString("ru")} ₽/мес · ${LOGISTICS_TRACKER_YEARLY.toLocaleString("ru")} ₽/год`,
              desc: "Склады, остатки, заказы, возвраты, рекомендации по пополнению",
            },
            {
              name: "Расширенная аналитика Amazon",
              price: "7 190 ₽/мес",
              desc: "Полная аналитика продаж и атрибуции на Amazon Marketplace",
            },
            {
              name: "Дополнительный магазин",
              price: `${EXTRA_STORE_PRICE.toLocaleString("ru")} ₽/мес`,
              desc: "Добавить ещё один магазин WB, Ozon или Яндекс.Маркет сверх лимита тарифа",
            },
            {
              name: "ИИ-ассистент (для Logistics Tracker)",
              price: "1 490 ₽/мес",
              desc: "ИИ-рекомендации по логистике без перехода на Business-тариф",
            },
            {
              name: "Пакет «Агентство» (от 5 магазинов)",
              price: "скидка 15% от базовой цены",
              desc: "Единый кабинет для управления несколькими магазинами клиентов",
            },
          ].map((a) => (
            <div key={a.name} className={styles.addon}>
              <div className={styles.addonLeft}>
                <p className={styles.addonName}>{a.name}</p>
                <p className={styles.addonDesc}>{a.desc}</p>
              </div>
              <p className={styles.addonPrice}>{a.price}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className={styles.faqSection} aria-label="Частые вопросы о тарифах">
        <h2 className={styles.sectionTitle}>Вопросы о тарифах</h2>
        <div className={styles.faqList}>
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className={`${styles.faqItem} ${openFaq === i ? styles.faqOpen : ""}`}
            >
              <button
                className={styles.faqQ}
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                aria-expanded={openFaq === i}
              >
                {faq.q}
                <span className={styles.faqChevron} aria-hidden>⌄</span>
              </button>
              <div className={styles.faqA}>{faq.a}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Enterprise lead form */}
      <section id="enterprise-form" className={styles.enterpriseSection} aria-label="Заявка на Enterprise">
        <div className={styles.enterpriseInner}>
          <h2 className={styles.enterpriseTitle}>Оставить заявку на Enterprise</h2>
          <p className={styles.enterpriseSub}>
            Индивидуальные условия, персональный менеджер, SLA 99.9%, интеграция с CRM и BI.
          </p>

          {formSent ? (
            <div className={styles.formSuccess}>
              ✓ Заявка принята! Свяжемся с вами в течение 1 рабочего дня.
            </div>
          ) : (
            <form className={styles.form} onSubmit={handleEnterpriseSubmit} noValidate>
              <div className={styles.formRow}>
                <label className={styles.formLabel}>
                  Имя *
                  <input className={styles.formInput} required value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })} />
                </label>
                <label className={styles.formLabel}>
                  Email *
                  <input className={styles.formInput} type="email" required value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })} />
                </label>
              </div>
              <div className={styles.formRow}>
                <label className={styles.formLabel}>
                  Телефон
                  <input className={styles.formInput} type="tel" value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })} />
                </label>
                <label className={styles.formLabel}>
                  Компания
                  <input className={styles.formInput} value={form.company}
                    onChange={(e) => setForm({ ...form, company: e.target.value })} />
                </label>
              </div>
              <label className={styles.formLabel}>
                Количество магазинов
                <input className={styles.formInput} type="number" min="1" value={form.stores}
                  onChange={(e) => setForm({ ...form, stores: e.target.value })} />
              </label>
              <button
                className={styles.formBtn}
                type="submit"
                disabled={formLoading || !form.name || !form.email}
              >
                {formLoading ? "Отправка…" : "Отправить заявку"}
              </button>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
