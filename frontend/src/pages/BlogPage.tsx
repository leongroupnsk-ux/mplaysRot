import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchBlogArticles, type BlogArticleCard } from "../api/blog";
import styles from "./BlogPage.module.css";

const CATEGORIES = [
  { value: "all",          label: "Все" },
  { value: "traffic",      label: "Внешний трафик" },
  { value: "logistics",    label: "Логистика" },
  { value: "analytics",    label: "Аналитика" },
  { value: "ai",           label: "AI" },
  { value: "integrations", label: "Интеграции" },
  { value: "news",         label: "Новости" },
];

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

function readingTime(excerpt: string | null) {
  const words = (excerpt ?? "").split(/\s+/).length;
  return Math.max(1, Math.round(words / 200)) + " мин";
}

function CategoryBadge({ cat }: { cat: string }) {
  const found = CATEGORIES.find((c) => c.value === cat);
  return <span className={styles.catBadge}>{found?.label ?? cat}</span>;
}

function ArticleCard({ article }: { article: BlogArticleCard }) {
  return (
    <Link to={`/blog/${article.slug}`} className={styles.card}>
      <div className={styles.cardCover}>
        {article.cover_image ? (
          <img src={article.cover_image} alt={article.title} loading="lazy" />
        ) : (
          <div className={styles.cardCoverPlaceholder}>📝</div>
        )}
        <CategoryBadge cat={article.category} />
        <div className={styles.cardOverlay}>
          <span className={styles.readMoreBtn}>Читать →</span>
        </div>
      </div>
      <div className={styles.cardBody}>
        <h2 className={styles.cardTitle}>{article.title}</h2>
        {article.excerpt && (
          <p className={styles.cardExcerpt}>{article.excerpt.slice(0, 160)}</p>
        )}
        <div className={styles.cardMeta}>
          <span className={styles.cardAuthor}>{article.author}</span>
          <span className={styles.cardDot}>·</span>
          <span>{formatDate(article.published_at)}</span>
          <span className={styles.cardDot}>·</span>
          <span>{readingTime(article.excerpt)}</span>
        </div>
        <div className={styles.cardStats}>
          <span title="Просмотры" className={styles.statItem}>👁 {article.view_count.toLocaleString("ru-RU")}</span>
          <span title="Лайки" className={styles.statItem}>❤️ {article.like_count}</span>
        </div>
      </div>
    </Link>
  );
}

export default function BlogPage() {
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [subscribedCategories, setSubscribedCategories] = useState<string[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: ["blog-articles", category, page, search],
    queryFn: () => fetchBlogArticles({
      page,
      category: category === "all" ? undefined : category,
      search: search || undefined,
    }),
    staleTime: 60_000,
  });

  const articles = data?.items ?? [];
  const totalPages = data?.pages ?? 1;

  const toggleCategorySubscription = (cat: string) => {
    setSubscribedCategories((prev) =>
      prev.includes(cat)
        ? prev.filter((c) => c !== cat)
        : [...prev, cat]
    );
  };

  return (
    <div className={styles.root}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <Link to="/" className={styles.logo}>MPlays</Link>
          <nav className={styles.nav}>
            <Link to="/blog" className={styles.navLink}>Блог</Link>
            <Link to="/pricing" className={styles.navLink}>Тарифы</Link>
            <Link to="/login" className={styles.navLink}>Войти</Link>
            <Link to="/register" className={styles.navCta}>Попробовать бесплатно</Link>
          </nav>
        </div>
      </header>

      <main className={styles.main}>
        {/* Hero */}
        <section className={styles.hero}>
          <h1 className={styles.heroTitle}>
            Блог MPlays — всё о внешнем трафике и логистике маркетплейсов
          </h1>
          <p className={styles.heroSub}>
            Экспертные статьи для селлеров WB, Ozon, Яндекс.Маркет: аналитика, атрибуция, AI и логистика.
          </p>
        </section>

        {/* Search */}
        <div className={styles.searchSection}>
          <input
            type="search"
            className={styles.searchInput}
            placeholder="Поиск по статьям…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        {/* Category filter */}
        <div className={styles.filters}>
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              className={`${styles.filterBtn} ${category === c.value ? styles.filterBtnActive : ""}`}
              onClick={() => { setCategory(c.value); setPage(1); }}
              title={`Нажмите для подписки на ${c.label}`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className={styles.layout}>
          {/* Article grid */}
          <div className={styles.gridCol}>
            {isLoading ? (
              <div className={styles.loading}>
                <div className={styles.loadingSpinner} />
                Загружаем статьи…
              </div>
            ) : articles.length === 0 ? (
              <div className={styles.empty}>
                <div className={styles.emptyIcon}>📝</div>
                <div className={styles.emptyTitle}>
                  {search ? "Ничего не найдено" : "Статьи скоро появятся"}
                </div>
                <div className={styles.emptyDesc}>
                  {search
                    ? `По запросу «${search}» статей не найдено. Попробуйте другой запрос или сбросьте фильтры.`
                    : "Мы уже готовим экспертные материалы о внешнем трафике, логистике и аналитике маркетплейсов."}
                </div>
                {search && (
                  <button
                    className={styles.emptyReset}
                    onClick={() => { setSearch(""); setCategory("all"); }}
                  >
                    Сбросить фильтры
                  </button>
                )}
              </div>
            ) : (
              <div className={styles.grid}>
                {articles.map((a) => (
                  <ArticleCard key={a.id} article={a} />
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className={styles.pagination}>
                <button
                  className={styles.pageBtn}
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                >
                  ← Назад
                </button>
                <span className={styles.pageInfo}>
                  {page} из {totalPages}
                </span>
                <button
                  className={styles.pageBtn}
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                >
                  Далее →
                </button>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside className={styles.sidebar}>
            {/* Popular articles */}
            <div className={styles.sideCard}>
              <div className={styles.sideTitle}>📊 Популярное</div>
              {(data?.items ?? [])
                .slice()
                .sort((a, b) => b.view_count - a.view_count)
                .slice(0, 5)
                .map((a) => (
                  <Link key={a.id} to={`/blog/${a.slug}`} className={styles.popularItem}>
                    <div className={styles.popularTitle}>{a.title}</div>
                    <div className={styles.popularMeta}>
                      👁 {a.view_count.toLocaleString("ru-RU")} · {formatDate(a.published_at)}
                    </div>
                  </Link>
                ))}
            </div>

            {/* Subscriptions */}
            <div className={styles.sideCard}>
              <div className={styles.sideTitle}>🔔 Подписки</div>
              <div className={styles.subscriptionsList}>
                {CATEGORIES.filter((c) => c.value !== "all").map((cat) => (
                  <label key={cat.value} className={styles.subscriptionItem}>
                    <input
                      type="checkbox"
                      checked={subscribedCategories.includes(cat.value)}
                      onChange={() => toggleCategorySubscription(cat.value)}
                    />
                    <span>{cat.label}</span>
                  </label>
                ))}
              </div>
              {subscribedCategories.length > 0 && (
                <p className={styles.subscriptionHint}>
                  Вы подписаны на {subscribedCategories.length} {
                    subscribedCategories.length === 1
                      ? "категорию"
                      : subscribedCategories.length < 5
                      ? "категории"
                      : "категорий"
                  }
                </p>
              )}
            </div>

            {/* CTA */}
            <div className={styles.sideCta}>
              <div className={styles.sideCtaTitle}>⚡ Узнайте реальный ROI</div>
              <p className={styles.sideCtaSub}>
                Подключите MPlays и увидите, какой канал приносит заказы. Бесплатно 14 дней.
              </p>
              <Link to="/register" className={styles.sideCtaBtn}>
                Попробовать бесплатно
              </Link>
            </div>

            {/* Newsletter */}
            <div className={styles.sideCard}>
              <div className={styles.sideTitle}>✉️ Рассылка</div>
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 10 }}>
                Лучшие статьи — раз в неделю.
              </p>
              <div style={{ display: "flex", gap: 6, flexDirection: "column" }}>
                <input
                  type="email"
                  placeholder="ваш@email.ru"
                  className={styles.emailInput}
                />
                <button className={styles.subscribeBtn}>Подписаться</button>
              </div>
            </div>
          </aside>
        </div>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span>© 2026 MPlays</span>
          <Link to="/pricing" className={styles.footerLink}>Тарифы</Link>
          <Link to="/blog" className={styles.footerLink}>Блог</Link>
        </div>
      </footer>
    </div>
  );
}
