import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchBlogArticle, fetchBlogArticles, registerView, toggleLike } from "../api/blog";
import styles from "./BlogArticlePage.module.css";

const CATEGORIES: Record<string, string> = {
  traffic: "Внешний трафик",
  logistics: "Логистика",
  analytics: "Аналитика",
  ai: "AI",
  integrations: "Интеграции",
  news: "Новости",
  general: "Блог",
};

function formatDate(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric", month: "long", year: "numeric",
  });
}

function readingTime(content: string | null) {
  const words = (content ?? "").replace(/<[^>]+>/g, "").split(/\s+/).length;
  return Math.max(1, Math.round(words / 200));
}

export default function BlogArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const [likeCount, setLikeCount] = useState<number | null>(null);
  const [liked, setLiked] = useState(false);
  const [likeLoading, setLikeLoading] = useState(false);

  const { data: article, isLoading, isError } = useQuery({
    queryKey: ["blog-article", slug],
    queryFn: () => fetchBlogArticle(slug!),
    enabled: !!slug,
    staleTime: 60_000,
  });

  // Related articles (same category)
  const { data: relatedData } = useQuery({
    queryKey: ["blog-articles", article?.category],
    queryFn: () => fetchBlogArticles({ category: article?.category }),
    enabled: !!article,
    staleTime: 120_000,
  });
  const related = (relatedData?.items ?? [])
    .filter((a) => a.slug !== slug)
    .slice(0, 3);

  // Register view once
  useEffect(() => {
    if (article?.id) {
      registerView(article.id).catch(() => null);
      setLikeCount(article.like_count);
      // Check cookie
      const key = `liked_${article.id}`;
      setLiked(document.cookie.includes(key));
    }
  }, [article?.id]);

  // Update document title for SEO
  useEffect(() => {
    if (article) {
      document.title = article.meta_title ?? article.title;
    }
  }, [article]);

  async function handleLike() {
    if (!article || likeLoading) return;
    setLikeLoading(true);
    try {
      const res = await toggleLike(article.id);
      setLikeCount(res.like_count);
      setLiked(res.liked);
    } catch {
      /* ignore */
    } finally {
      setLikeLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className={styles.root}>
        <BlogHeader />
        <main className={styles.main}>
          <div className={styles.loadingMsg}>Загружаем статью…</div>
        </main>
      </div>
    );
  }

  if (isError || !article) {
    return (
      <div className={styles.root}>
        <BlogHeader />
        <main className={styles.main}>
          <div className={styles.errorState}>
            <div>🔍</div>
            <div>Статья не найдена</div>
            <Link to="/blog" className={styles.backLink}>← Все статьи</Link>
          </div>
        </main>
      </div>
    );
  }

  const catLabel = CATEGORIES[article.category] ?? article.category;
  const mins = readingTime(article.content);

  return (
    <div className={styles.root}>
      {/* SEO meta via helmet would go here — basic title set in useEffect */}
      <BlogHeader />

      <main className={styles.main}>
        {/* Breadcrumbs */}
        <nav className={styles.breadcrumbs} aria-label="breadcrumb">
          <Link to="/" className={styles.breadLink}>Главная</Link>
          <span className={styles.breadSep}>›</span>
          <Link to="/blog" className={styles.breadLink}>Блог</Link>
          <span className={styles.breadSep}>›</span>
          <Link to={`/blog?category=${article.category}`} className={styles.breadLink}>
            {catLabel}
          </Link>
          <span className={styles.breadSep}>›</span>
          <span className={styles.breadCurrent}>{article.title}</span>
        </nav>

        <div className={styles.articleWrap}>
          {/* Article */}
          <article className={styles.article}>
            {/* Meta */}
            <header className={styles.articleHeader}>
              <span className={styles.catTag}>{catLabel}</span>
              <h1 className={styles.articleTitle}>{article.title}</h1>
              <div className={styles.articleMeta}>
                <span className={styles.author}>✍️ {article.author}</span>
                <span className={styles.metaDot}>·</span>
                <span>{formatDate(article.published_at)}</span>
                <span className={styles.metaDot}>·</span>
                <span>{mins} мин. чтения</span>
                <span className={styles.metaDot}>·</span>
                <span>👁 {(article.view_count).toLocaleString("ru-RU")}</span>
              </div>
            </header>

            {/* Cover */}
            {article.cover_image && (
              <div className={styles.coverWrap}>
                <img
                  src={article.cover_image}
                  alt={article.title}
                  className={styles.cover}
                  loading="eager"
                />
              </div>
            )}

            {/* Content */}
            {article.content && (
              <div
                className={styles.content}
                dangerouslySetInnerHTML={{ __html: article.content }}
              />
            )}

            {/* Like block */}
            <div className={styles.likeBlock}>
              <div className={styles.likeTitle}>Понравилась статья?</div>
              <button
                className={`${styles.likeBtn} ${liked ? styles.likeBtnActive : ""}`}
                onClick={handleLike}
                disabled={likeLoading}
              >
                {liked ? "❤️" : "🤍"} {likeCount ?? article.like_count}
              </button>
              <a
                href="https://t.me/attribly"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.telegramBtn}
              >
                Обсудить в Telegram →
              </a>
            </div>

            {/* Tags */}
            {article.tags.length > 0 && (
              <div className={styles.tags}>
                {article.tags.map((t) => (
                  <span key={t} className={styles.tag}>#{t}</span>
                ))}
              </div>
            )}
          </article>

          {/* Sidebar */}
          <aside className={styles.sidebar}>
            {/* CTA */}
            <div className={styles.ctaCard}>
              <div className={styles.ctaTitle}>
                Узнайте, какой источник трафика реально приносит заказы
              </div>
              <p className={styles.ctaSub}>
                Подключите WB, Ozon и рекламные кабинеты за 5 минут. 14 дней бесплатно.
              </p>
              <Link to="/register" className={styles.ctaBtn}>
                Попробовать MPlays бесплатно
              </Link>
            </div>
          </aside>
        </div>

        {/* Related articles */}
        {related.length > 0 && (
          <section className={styles.related}>
            <h2 className={styles.relatedTitle}>Похожие статьи</h2>
            <div className={styles.relatedGrid}>
              {related.map((a) => (
                <Link key={a.id} to={`/blog/${a.slug}`} className={styles.relatedCard}>
                  {a.cover_image && (
                    <img src={a.cover_image} alt={a.title} className={styles.relatedCover} loading="lazy" />
                  )}
                  <div className={styles.relatedBody}>
                    <div className={styles.relatedCat}>{CATEGORIES[a.category] ?? a.category}</div>
                    <div className={styles.relatedCardTitle}>{a.title}</div>
                    <div className={styles.relatedMeta}>{formatDate(a.published_at)} · 👁 {a.view_count}</div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Bottom CTA */}
        <div className={styles.bottomCta}>
          <div className={styles.bottomCtaText}>
            MPlays связывает каждый рекламный клик с заказом на WB и Ozon.
          </div>
          <Link to="/register" className={styles.bottomCtaBtn}>
            Попробовать бесплатно — 14 дней
          </Link>
        </div>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span>© 2026 MPlays</span>
          <Link to="/blog" className={styles.footerLink}>Блог</Link>
          <Link to="/pricing" className={styles.footerLink}>Тарифы</Link>
        </div>
      </footer>
    </div>
  );
}

function BlogHeader() {
  return (
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
  );
}
