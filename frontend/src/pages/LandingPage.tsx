import { useState, useEffect, useCallback, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { login as apiLogin, register as apiRegister, fetchMe } from "../api/auth";
import { LANDING_PLANS, LOGISTICS_TRACKER_MONTHLY, LOGISTICS_TRACKER_YEARLY, EXTRA_STORE_PRICE, ANNUAL_DISCOUNT } from "../constants/pricing";
import styles from "./LandingPage.module.css";

// ── Scroll-reveal hook ────────────────────────────────────────────────────────
function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll<HTMLElement>(`.${styles.reveal}`);
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add(styles.visible);
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

// ── Auth modal ────────────────────────────────────────────────────────────────
type AuthTab = "login" | "register";

interface AuthModalProps {
  initialTab: AuthTab;
  onClose: () => void;
}

function AuthModal({ initialTab, onClose }: AuthModalProps) {
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();

  const [tab, setTab] = useState<AuthTab>(initialTab);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetForm = useCallback((t: AuthTab) => {
    setTab(t);
    setError(null);
    setFullName("");
    setEmail("");
    setPassword("");
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    if (tab === "register" && password.length < 8) {
      setError("Пароль должен содержать не менее 8 символов.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const tokens =
        tab === "login"
          ? await apiLogin(email, password)
          : await apiRegister(email, password, fullName || undefined);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await fetchMe();
      setUser(me);
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } }).response?.status;
      if (tab === "login") {
        setError(status === 401 || status === 403 ? "Неверный email или пароль." : "Ошибка сервера. Попробуйте позже.");
      } else {
        if (status === 409) setError("Этот email уже зарегистрирован.");
        else if (status === 422) setError("Проверьте правильность введённых данных.");
        else setError("Ошибка сервера. Попробуйте позже.");
      }
    } finally {
      setLoading(false);
    }
  };

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className={styles.modalOverlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modalCard} role="dialog" aria-modal="true" aria-label="Авторизация">
        <div className={styles.modalHeader}>
          <div className={styles.modalTabs}>
            <button className={`${styles.modalTab} ${tab === "login" ? styles.active : ""}`} onClick={() => resetForm("login")}>
              Вход
            </button>
            <button className={`${styles.modalTab} ${tab === "register" ? styles.active : ""}`} onClick={() => resetForm("register")}>
              Регистрация
            </button>
          </div>
          <button className={styles.modalClose} onClick={onClose} aria-label="Закрыть">×</button>
        </div>

        <form className={styles.authForm} onSubmit={handleSubmit} noValidate>
          {tab === "register" && (
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="modal-name">Имя <span style={{ opacity: 0.5 }}>(необязательно)</span></label>
              <input id="modal-name" className={styles.formInput} type="text" value={fullName}
                onChange={(e) => setFullName(e.target.value)} placeholder="Иван Иванов" autoComplete="name" />
            </div>
          )}

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="modal-email">Email</label>
            <input id="modal-email" className={styles.formInput} type="email" value={email}
              onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com"
              autoComplete="email" required autoFocus />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="modal-password">Пароль</label>
            <input id="modal-password" className={styles.formInput} type="password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === "register" ? "Не менее 8 символов" : "••••••••"}
              autoComplete={tab === "login" ? "current-password" : "new-password"} required />
          </div>

          {error && <div className={styles.formError}>{error}</div>}

          <button className={styles.btnSubmit} type="submit" disabled={loading || !email || !password}>
            {loading ? "Загрузка…" : tab === "login" ? "Войти" : "Создать аккаунт"}
          </button>
        </form>

        <p className={styles.formFooter} style={{ marginTop: 16 }}>
          {tab === "login" ? "Нет аккаунта?" : "Уже есть аккаунт?"}
          <button className={styles.formFooterLink} onClick={() => resetForm(tab === "login" ? "register" : "login")}>
            {tab === "login" ? "Зарегистрироваться" : "Войти"}
          </button>
        </p>
      </div>
    </div>
  );
}

// ── Data ──────────────────────────────────────────────────────────────────────
const BENEFITS = [
  {
    icon: "📊",
    title: "Сквозная атрибуция",
    tip: "Связывает каждый клик рекламы с конкретным заказом",
    desc: "Узнайте, какая реклама реально приносит заказы — даже на Wildberries и Amazon без доступа к данным о покупателе.",
  },
  {
    icon: "🤖",
    title: "Автооптимизация",
    tip: "Lookalike-сегменты на основе ваших лучших покупателей",
    desc: "Look-alike аудитории и умная остановка неэффективных кампаний прямо из платформы.",
  },
  {
    icon: "📦",
    title: "Контроль остатков",
    tip: "Данные со всех складов WB обновляются каждые 15 минут",
    desc: "Не теряйте продажи из-за дефицита. Система предупредит за 7 дней до обнуления остатков.",
  },
  {
    icon: "🔒",
    title: "Безопасность данных",
    tip: "AES-256-GCM шифрование, ключи никогда не покидают сервер",
    desc: "Все API-ключи шифруются алгоритмом AES-256. Аналитические данные хранятся в соответствии с ФЗ-152.",
  },
];

const MODULES = [
  {
    emoji: "📈",
    title: "Сквозная аналитика и атрибуция",
    desc: "Полная воронка от клика до заказа. Понимайте реальную эффективность каждого источника трафика.",
    features: ["Прямая атрибуция для Ozon и Яндекс.Маркета", "Вероятностная модель для WB и Amazon", "Сравнение периодов, гео-аналитика"],
  },
  {
    emoji: "🎯",
    title: "Управление рекламными кампаниями",
    desc: "Создавайте и отслеживайте кампании во всех каналах из одного окна.",
    features: ["Генератор трекинг-ссылок с UTM-разметкой", "Яндекс.Директ, VK Ads, Telegram Ads", "Дневные лимиты и автостоп по ROAS"],
  },
  {
    emoji: "🚚",
    title: "Logistics Tracker (Wildberries)",
    desc: "Полный контроль остатков, заказов и возвратов на складах Wildberries.",
    features: ["Остатки по складам и размерам", "Дни запаса и предупреждения о дефиците", "Аналитика возвратов по причинам"],
  },
  {
    emoji: "🤖",
    title: "ИИ-ассистент и рекомендации",
    desc: "Задавайте вопросы в свободной форме — ИИ анализирует ваши данные и предлагает план действий.",
    features: ["Рекомендации по пополнению товаров", "Анализ причин высоких возвратов", "Чат-интерфейс с контекстом вашего магазина"],
  },
  {
    emoji: "👥",
    title: "Аудитории и Look-alike",
    desc: "Превратите своих лучших покупателей в источник новых клиентов через рекламные кабинеты.",
    features: ["Сегменты на основе покупателей с высоким ROAS", "Активация в VK Ads и Яндекс.Директ", "История активаций и результаты"],
  },
  {
    emoji: "🔌",
    title: "Интеграции и безопасность",
    desc: "Подключайте все площадки через единый интерфейс. Ключи хранятся в зашифрованном виде.",
    features: ["Ozon, WB, Яндекс.Маркет, Amazon", "AES-256-GCM шифрование ключей", "Единый дашборд для всех магазинов"],
  },
];

const STEPS = [
  { icon: "🔌", title: "Подключите источники", desc: "Интеграция с маркетплейсами и рекламными кабинетами в пару кликов." },
  { icon: "🔗", title: "Сгенерируйте ссылки", desc: "Система сама подберёт артикулы и создаст UTM-метки для каждой кампании." },
  { icon: "📊", title: "Анализируйте в реальном времени", desc: "Вся аналитика от клика до заказа на одном дашборде." },
  { icon: "⚡", title: "Оптимизируйте с AI", desc: "Получайте рекомендации и автоматически корректируйте кампании." },
];

const FAQS = [
  { q: "На каких маркетплейсах работает MPlays?", a: "MPlays поддерживает Ozon, Wildberries, Яндекс.Маркет и Amazon. Для Ozon и ЯМ доступна прямая атрибуция через Performance API. Для WB и Amazon — вероятностная модель на базе машинного обучения." },
  { q: "Как быстро я увижу результаты?", a: "Данные о кликах появляются в режиме реального времени. Первые атрибутированные заказы — в течение 24 часов после настройки кампаний. ML-модель атрибуции начинает работать с момента накопления первых 100 совпадений." },
  { q: "Нужно ли что-то устанавливать на сайт или в магазин?", a: "Нет. MPlays работает через API маркетплейсов и рекламных кабинетов. Вы просто подключаете интеграции в личном кабинете — без кода и технических знаний." },
  { q: "Безопасно ли подключать API-ключи?", a: "Да. Все ключи шифруются алгоритмом AES-256-GCM на стороне сервера. Ключ шифрования хранится отдельно и никогда не передаётся клиенту. Доступ к ключам имеет только ваш аккаунт." },
  { q: "Что делать, если у меня несколько магазинов?", a: "Все ваши магазины отображаются в едином дашборде. Вы можете переключаться между ними, сравнивать метрики и управлять кампаниями для каждого независимо." },
];

const TESTIMONIALS = [
  {
    name: "Ирина Петрова",
    company: "Beauty & Style (WB)",
    avatar: "👩‍💼",
    text: "Раньше мы сливали половину бюджета на неэффективные каналы и не знали почему. MPlays за неделю показал, где деньги. Увеличили выручку на 34% за счёт переоптимизации.",
    metric: "34% ↑ выручка",
  },
  {
    name: "Владимир Иванов",
    company: "TechParts (Ozon + Amazon)",
    avatar: "👨‍💼",
    text: "До MPlays интегрировали каждый маркетплейс отдельно. Теперь один дашборд для всего. Экономим 15 часов в неделю на аналитике и отчётах.",
    metric: "15 часов/неделю",
  },
  {
    name: "Мария Сидорова",
    company: "FashionHub (ЯМ + WB)",
    avatar: "👩‍🎨",
    text: "AI-ассистент просто спасение. Вместо того, чтобы копать в таблицах, спрашиваю его «почему упали продажи носков в ЛО?» — и мгновенно получаю анализ с рекомендациями.",
    metric: "ИИ рекомендации",
  },
];

const CASE_STUDIES = [
  {
    title: "Как селлер WB увеличил ROAS с 2.1 до 3.8 за месяц",
    category: "Кейс",
    excerpt: "История автоматизации, правильной атрибуции и нейросетей, которые помогли за 30 дней перестроить рекламную стратегию.",
  },
  {
    title: "Logistics Tracker спас 4.2М на возвратах",
    category: "Практика",
    excerpt: "Как контроль остатков предотвратил переизбыток товара на складах WB и освободил оборотные средства.",
  },
  {
    title: "Multi-store аналитика: управляем 3 магазинами из одного дашборда",
    category: "Опыт",
    excerpt: "Как компания с товарами на Ozon, WB и Amazon сократила время на консолидацию отчётов с 8 часов до 20 минут.",
  },
];

const CHART_BARS = [35, 52, 41, 68, 79, 61, 88, 72, 95, 84, 90, 100];

// ── Landing Page ──────────────────────────────────────────────────────────────
export default function LandingPage() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const [burgerOpen, setBurgerOpen] = useState(false);
  const [modal, setModal] = useState<AuthTab | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [earlyEmail, setEarlyEmail] = useState("");
  const [earlySubmitted, setEarlySubmitted] = useState(false);
  const [earlyLoading, setEarlyLoading] = useState(false);

  useReveal();

  const scrollTo = (id: string) => {
    setBurgerOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  const openModal = (tab: AuthTab) => {
    if (isAuthenticated) { navigate("/dashboard"); return; }
    setModal(tab);
    document.body.style.overflow = "hidden";
  };
  const closeModal = () => {
    setModal(null);
    document.body.style.overflow = "";
  };

  const handleEarlyAccess = async (e: FormEvent) => {
    e.preventDefault();
    if (!earlyEmail) return;
    setEarlyLoading(true);
    await new Promise((r) => setTimeout(r, 800));
    setEarlySubmitted(true);
    setEarlyLoading(false);
  };

  return (
    <div className={styles.page}>
      {/* ── SEO meta (injected via index.html in production) ── */}

      {/* ── Header ─────────────────────────────────────────── */}
      <header className={styles.header}>
        <a className={styles.logo} href="/" aria-label="MPlays — на главную">
          <div className={styles.logoMark} aria-hidden>A</div>
          MPlays
        </a>

        <nav className={styles.nav} aria-label="Основная навигация">
          <button className={styles.navLink} onClick={() => scrollTo("benefits")}>Возможности</button>
          <button className={styles.navLink} onClick={() => scrollTo("modules")}>Модули</button>
          <button className={styles.navLink} onClick={() => scrollTo("cases")}>Кейсы</button>
          <button className={styles.navLink} onClick={() => scrollTo("pricing")}>Тарифы</button>
          <button className={styles.navLink} onClick={() => scrollTo("faq")}>FAQ</button>
        </nav>

        <div className={styles.headerActions}>
          {isAuthenticated ? (
            <button className={styles.btnPrimary} onClick={() => navigate("/dashboard")}>Личный кабинет</button>
          ) : (
            <>
              <button className={styles.btnOutline} onClick={() => openModal("login")}>Войти</button>
              <button className={styles.btnPrimary} onClick={() => openModal("register")}>Регистрация</button>
            </>
          )}
        </div>

        <button
          className={`${styles.burger} ${burgerOpen ? styles.open : ""}`}
          onClick={() => setBurgerOpen(!burgerOpen)}
          aria-label={burgerOpen ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={burgerOpen}
        >
          <span className={styles.burgerLine} />
          <span className={styles.burgerLine} />
          <span className={styles.burgerLine} />
        </button>
      </header>

      {/* Mobile nav */}
      <nav className={`${styles.mobileNav} ${burgerOpen ? styles.open : ""}`} aria-label="Мобильная навигация">
        <button className={styles.mobileNavLink} onClick={() => scrollTo("benefits")}>Возможности</button>
        <button className={styles.mobileNavLink} onClick={() => scrollTo("modules")}>Модули</button>
        <button className={styles.mobileNavLink} onClick={() => scrollTo("cases")}>Кейсы</button>
        <button className={styles.mobileNavLink} onClick={() => scrollTo("pricing")}>Тарифы</button>
        <button className={styles.mobileNavLink} onClick={() => scrollTo("faq")}>FAQ</button>
        <div className={styles.mobileActions}>
          <button className={styles.btnOutline} style={{ flex: 1 }} onClick={() => openModal("login")}>Войти</button>
          <button className={styles.btnPrimary} style={{ flex: 1 }} onClick={() => openModal("register")}>Регистрация</button>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────── */}
      <main>
        <section id="hero" className={styles.hero} aria-label="Главный экран">
          <div className={styles.heroGlow} aria-hidden />
          <div className={styles.heroBadge}>Платформа для селлеров маркетплейсов</div>
          <h1 className={styles.heroTitle}>
            Управляйте внешним трафиком{" "}
            <span className={styles.heroAccent}>прозрачно</span>{" "}
            и без потерь
          </h1>
          <p className={styles.heroSub}>
            MPlays — единая платформа атрибуции, аналитики и AI-рекомендаций
            для селлеров Ozon, Wildberries, Яндекс.Маркета и Amazon.
          </p>
          <div className={styles.heroActions}>
            <button className={styles.btnHero} onClick={() => openModal("register")}>
              Попробовать бесплатно
            </button>
            <button className={styles.btnHeroGhost} onClick={() => scrollTo("modules")}>
              Узнать подробнее
            </button>
          </div>

          {/* Dashboard preview */}
          <div className={styles.heroDashboard} aria-hidden>
            <div className={styles.dashboardBar}>
              <span className={styles.dot} /><span className={styles.dot} /><span className={styles.dot} />
            </div>
            <div className={styles.dashboardMetrics}>
              {[
                { label: "ROAS", value: "4.2×", up: "+12%" },
                { label: "Заказы (атрибут.)", value: "1 847", up: "+8%" },
                { label: "Бюджет", value: "₽284K", up: "−3%" },
                { label: "AOV", value: "₽3 210", up: "+5%" },
              ].map((m) => (
                <div key={m.label} className={styles.dashMetric}>
                  <div className={styles.dashMetricLabel}>{m.label}</div>
                  <div className={styles.dashMetricValue}>{m.value}</div>
                  <div className={styles.dashMetricUp}>{m.up}</div>
                </div>
              ))}
            </div>
            <div className={styles.dashChart}>
              {CHART_BARS.map((h, i) => (
                <div key={i} className={styles.chartBar} style={{ height: `${h}%` }} />
              ))}
            </div>
          </div>
        </section>

        {/* ── Benefits ─────────────────────────────────────── */}
        <section id="benefits" aria-label="Преимущества">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Почему MPlays</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Всё, что нужно для роста продаж</h2>
            <p className={`${styles.sectionSub} ${styles.reveal}`}>
              Решаем ключевые боли селлеров: непрозрачность атрибуции, потери из-за дефицита и слепые ставки в рекламе.
            </p>
            <div className={styles.benefitsGrid}>
              {BENEFITS.map((b) => (
                <article key={b.title} className={`${styles.benefitCard} ${styles.reveal}`}>
                  <div className={styles.benefitIcon} aria-hidden>{b.icon}</div>
                  <h3 className={styles.benefitTitle}>
                    {b.title}
                    <span
                      className={`${styles.tooltip} ${styles.tooltipIcon}`}
                      data-tip={b.tip}
                      tabIndex={0}
                      role="note"
                      aria-label={b.tip}
                    >i</span>
                  </h3>
                  <p className={styles.benefitDesc}>{b.desc}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── Modules ──────────────────────────────────────── */}
        <section id="modules" className={styles.modulesBg} aria-label="Модули платформы">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Модули платформы</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Полный набор инструментов селлера</h2>
            <p className={`${styles.sectionSub} ${styles.reveal}`}>
              Шесть взаимосвязанных модулей покрывают весь цикл: трафик → атрибуция → логистика → оптимизация.
            </p>
            <div className={styles.modulesGrid}>
              {MODULES.map((m) => (
                <article key={m.title} className={`${styles.moduleCard} ${styles.reveal}`}>
                  <div className={styles.moduleEmoji} aria-hidden>{m.emoji}</div>
                  <h3 className={styles.moduleTitle}>{m.title}</h3>
                  <p className={styles.moduleDesc}>{m.desc}</p>
                  <ul className={styles.moduleFeatures} aria-label="Ключевые функции">
                    {m.features.map((f) => <li key={f}>{f}</li>)}
                  </ul>
                  <button className={styles.moduleLink} onClick={() => openModal("register")}>
                    Попробовать →
                  </button>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── How it works ─────────────────────────────────── */}
        <section id="how" aria-label="Как это работает">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Как это работает</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Запустите аналитику за 4 шага</h2>
            <p className={`${styles.sectionSub} ${styles.reveal}`}>
              От подключения первого магазина до первых инсайтов — меньше часа.
            </p>
            <div className={styles.stepsGrid}>
              {STEPS.map((s, i) => (
                <div key={s.title} className={`${styles.step} ${styles.reveal}`}>
                  <div className={styles.stepNum} aria-hidden>{s.icon}</div>
                  <h3 className={styles.stepTitle}>
                    <span style={{ color: "var(--text-muted)", marginRight: 6 }}>{i + 1}.</span>
                    {s.title}
                  </h3>
                  <p className={styles.stepDesc}>{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Pricing ──────────────────────────────────────── */}
        <section id="pricing" aria-label="Тарифы">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Тарифы</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Выберите подходящий план</h2>
            <p className={`${styles.sectionSub} ${styles.reveal}`} style={{ margin: "0 auto" }}>
              Годовая подписка — скидка {Math.round(ANNUAL_DISCOUNT * 100)}% (2 месяца в подарок).
            </p>

            {/* Three main cards: Free / Start / Business */}
            <div className={`${styles.pricingGrid} ${styles.reveal}`}>
              {LANDING_PLANS.map((plan) => (
                <div
                  key={plan.id}
                  className={`${styles.pricingCard} ${plan.highlighted ? styles.pricingCardHighlighted : ""}`}
                >
                  {plan.badge && (
                    <div className={styles.pricingBadge}>{plan.badge}</div>
                  )}
                  <div className={styles.pricingName}>{plan.name}</div>
                  <div className={styles.pricingDesc}>{plan.description}</div>
                  <div className={styles.pricingPrice}>
                    <span className={styles.pricingAmount}>{plan.priceLabel}</span>
                    <span className={styles.pricingPeriod}>{plan.period}</span>
                  </div>
                  <ul className={styles.pricingFeatures}>
                    {plan.features.map((f) => (
                      <li key={f.label} className={`${styles.pricingFeature} ${f.available ? "" : styles.pricingFeatureOff}`}>
                        <span className={styles.pricingFeatureIcon} aria-hidden>{f.available ? "✓" : "✕"}</span>
                        <span className={styles.pricingFeatureLabel}>{f.label}</span>
                        <span className={styles.pricingFeatureValue}>{f.value}</span>
                      </li>
                    ))}
                  </ul>
                  <button
                    className={plan.highlighted ? styles.btnPrimary : styles.btnOutline}
                    style={{ width: "100%", marginTop: "auto" }}
                    onClick={() => openModal("register")}
                  >
                    {plan.cta}
                  </button>
                </div>
              ))}
            </div>

            {/* Enterprise strip */}
            <div className={`${styles.enterpriseStrip} ${styles.reveal}`}>
              <div className={styles.enterpriseStripLeft}>
                <span className={styles.enterpriseStripName}>Enterprise</span>
                <span className={styles.enterpriseStripPrice}>от 47 990 ₽/мес</span>
                <span className={styles.enterpriseStripDesc}>
                  Неограниченные магазины и переходы · ML-атрибуция + ручная верификация · ИИ-ассистент без ограничений
                </span>
              </div>
              <a
                className={styles.btnPrimary}
                href="https://t.me/attribly"
                target="_blank"
                rel="noopener noreferrer"
              >
                Написать в Telegram
              </a>
            </div>

            {/* ROI value props */}
            <div className={`${styles.roiGrid} ${styles.reveal}`}>
              {[
                {
                  icon: "📈",
                  title: "Окупаемость от 1610%",
                  desc: "При перераспределении бюджета ROMI вырастает на 20–40%. Business-тариф окупается при бюджете от 100 000 ₽/мес.",
                },
                {
                  icon: "📦",
                  title: "Предотвращение out-of-stock",
                  desc: "Logistics Tracker предупреждает дефицит. При 200 заказах/мес с чеком 1 500 ₽ — это 300 000 ₽ упущенной выручки.",
                },
                {
                  icon: "🎯",
                  title: "ML-атрибуция вместо last-click",
                  desc: "Вероятностная модель точнее распределяет кредит между каналами — экономия бюджета без потери ROAS.",
                },
              ].map((item) => (
                <div key={item.title} className={styles.roiCard}>
                  <div className={styles.roiIcon}>{item.icon}</div>
                  <div className={styles.roiTitle}>{item.title}</div>
                  <div className={styles.roiDesc}>{item.desc}</div>
                </div>
              ))}
            </div>

            {/* Add-ons */}
            <div className={`${styles.pricingAddons} ${styles.reveal}`}>
              <p className={styles.pricingAddonsTitle}>Дополнительные опции</p>
              <div className={styles.pricingAddonsList}>
                <div className={styles.pricingAddon}>
                  <span className={styles.pricingAddonName}>Logistics Tracker (отдельный модуль)</span>
                  <span className={styles.pricingAddonPrice}>{LOGISTICS_TRACKER_MONTHLY.toLocaleString("ru")} ₽/мес · {LOGISTICS_TRACKER_YEARLY.toLocaleString("ru")} ₽/год</span>
                </div>
                <div className={styles.pricingAddon}>
                  <span className={styles.pricingAddonName}>Расширенная аналитика Amazon</span>
                  <span className={styles.pricingAddonPrice}>7 190 ₽/мес</span>
                </div>
                <div className={styles.pricingAddon}>
                  <span className={styles.pricingAddonName}>Дополнительный магазин</span>
                  <span className={styles.pricingAddonPrice}>{EXTRA_STORE_PRICE.toLocaleString("ru")} ₽/мес</span>
                </div>
                <div className={styles.pricingAddon}>
                  <span className={styles.pricingAddonName}>Пакет «Агентство» (от 5 магазинов)</span>
                  <span className={styles.pricingAddonPrice}>скидка 15% от базовой цены</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Early Access ─────────────────────────────────── */}
        <section className={`${styles.sectionFull} ${styles.earlyBg}`} aria-label="Ранний доступ">
          <div className={styles.earlyInner}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Ранний доступ</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>
              Присоединяйтесь первыми
            </h2>
            <p className={`${styles.sectionSub} ${styles.reveal}`} style={{ margin: "0 auto" }}>
              Оставьте email и получите приглашение в числе первых — с расширенным пробным периодом и прямым доступом к команде.
            </p>
            <form className={`${styles.earlyForm} ${styles.reveal}`} onSubmit={handleEarlyAccess} noValidate>
              <input
                className={styles.earlyInput}
                type="email"
                placeholder="your@company.com"
                value={earlyEmail}
                onChange={(e) => setEarlyEmail(e.target.value)}
                required
                aria-label="Email для раннего доступа"
              />
              <button className={styles.btnEarly} type="submit" disabled={earlyLoading || !earlyEmail}>
                {earlyLoading ? "Отправка…" : "Получить доступ"}
              </button>
            </form>
            {earlySubmitted && (
              <p className={styles.earlySuccess}>
                ✓ Заявка принята! Мы напишем вам на {earlyEmail}.
              </p>
            )}
            <p className={`${styles.earlyNote} ${styles.reveal}`}>
              Без спама. Только важные обновления и дата запуска.
            </p>
          </div>
        </section>

        {/* ── Testimonials ──────────────────────────────── */}
        <section id="testimonials" aria-label="Отзывы клиентов">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Отзывы</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Что говорят селлеры</h2>
            <div className={`${styles.testimonialsGrid} ${styles.reveal}`}>
              {TESTIMONIALS.map((t, i) => (
                <div key={i} className={`${styles.testimonial} ${styles.reveal}`}>
                  <div className={styles.testimonialAvatar}>{t.avatar}</div>
                  <p className={styles.testimonialText}>"{t.text}"</p>
                  <div className={styles.testimonialAuthor}>{t.name}</div>
                  <div className={styles.testimonialCompany}>{t.company}</div>
                  <div className={styles.testimonialMetric}>{t.metric}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Case Studies ──────────────────────────────── */}
        <section id="cases" aria-label="Кейсы и примеры">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>Кейсы</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Реальные примеры результатов</h2>
            <div className={`${styles.casesGrid} ${styles.reveal}`}>
              {CASE_STUDIES.map((cs, i) => (
                <div key={i} className={`${styles.caseCard} ${styles.reveal}`}>
                  <div className={styles.caseCategory}>{cs.category}</div>
                  <h3 className={styles.caseTitle}>{cs.title}</h3>
                  <p className={styles.caseExcerpt}>{cs.excerpt}</p>
                  <a href="#" className={styles.caseLink}>
                    Прочитать кейс →
                  </a>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── FAQ ──────────────────────────────────────────── */}
        <section id="faq" aria-label="Часто задаваемые вопросы">
          <div className={styles.section}>
            <p className={`${styles.sectionLabel} ${styles.reveal}`}>FAQ</p>
            <h2 className={`${styles.sectionTitle} ${styles.reveal}`}>Частые вопросы</h2>
            <div className={`${styles.faqList} ${styles.reveal}`}>
              {FAQS.map((faq, i) => (
                <div
                  key={i}
                  className={`${styles.faqItem} ${openFaq === i ? styles.open : ""}`}
                >
                  <button
                    className={styles.faqQuestion}
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    aria-expanded={openFaq === i}
                  >
                    {faq.q}
                    <span className={styles.faqChevron} aria-hidden>⌄</span>
                  </button>
                  <div className={styles.faqAnswer} role="region" aria-hidden={openFaq !== i}>
                    {faq.a}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className={styles.footer} aria-label="Подвал сайта">
        <div className={styles.footerInner}>
          <div className={styles.footerTop}>
            <div className={styles.footerBrand}>
              <a className={styles.logo} href="/" aria-label="MPlays">
                <div className={styles.logoMark} aria-hidden>A</div>
                MPlays
              </a>
              <p className={styles.footerBrandDesc}>
                Единая платформа атрибуции и аналитики для селлеров маркетплейсов.
              </p>
            </div>

            <div className={styles.footerCol}>
              <p className={styles.footerColTitle}>Продукт</p>
              <div className={styles.footerLinks}>
                <button className={styles.footerLink} onClick={() => scrollTo("modules")}>Модули</button>
                <button className={styles.footerLink} onClick={() => scrollTo("pricing")}>Тарифы</button>
                <button className={styles.footerLink} onClick={() => scrollTo("how")}>Как это работает</button>
              </div>
            </div>

            <div className={styles.footerCol}>
              <p className={styles.footerColTitle}>Ресурсы</p>
              <div className={styles.footerLinks}>
                <a className={styles.footerLink} href="mailto:hello@mplays.ru">Контакты</a>
                <Link className={styles.footerLink} to="/blog">Блог</Link>
                <Link className={styles.footerLink} to="/pricing">Тарифы</Link>
              </div>
            </div>

            <div className={styles.footerCol}>
              <p className={styles.footerColTitle}>Правовое</p>
              <div className={styles.footerLinks}>
                <a className={styles.footerLink} href="#">Политика конфиденциальности</a>
                <a className={styles.footerLink} href="#">Условия использования</a>
              </div>
            </div>
          </div>

          <div className={styles.footerBottom}>
            <p className={styles.footerCopy}>© 2026 MPlays. Все права защищены.</p>
            <div className={styles.socialLinks}>
              <a href="#" className={styles.socialLink} aria-label="Telegram" rel="noopener noreferrer">✈</a>
              <a href="#" className={styles.socialLink} aria-label="YouTube" rel="noopener noreferrer">▶</a>
              <a href="#" className={styles.socialLink} aria-label="VC.ru" rel="noopener noreferrer">V</a>
            </div>
          </div>
        </div>
      </footer>

      {/* ── Auth Modal ───────────────────────────────────── */}
      {modal && <AuthModal initialTab={modal} onClose={closeModal} />}
    </div>
  );
}
