/**
 * Public page: /l/:code
 *
 * - For deeplinks: immediately attempts to open the marketplace app via URI scheme,
 *   then falls back to the web URL. Shows a minimal card while the redirect happens.
 * - For autolandings: shows a full product card with "Open in app" / "Go to website" buttons.
 */
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { resolveLink, trackClick, buildMarketplaceUri, buildWebUrl, type DeepLinkPublic } from "../api/links";
import css from "./LandingRedirectPage.module.css";

const MARKETPLACE_LABELS: Record<string, string> = {
  wildberries: "Wildberries",
  ozon: "Ozon",
};

function detectDevice(): string {
  const ua = navigator.userAgent.toLowerCase();
  if (/(ipad|tablet|kindle)/.test(ua)) return "tablet";
  if (/(mobile|android|iphone|ipod)/.test(ua)) return "mobile";
  return "desktop";
}

export default function LandingRedirectPage() {
  const { code } = useParams<{ code: string }>();
  const [link, setLink] = useState<DeepLinkPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    if (!code) return;
    resolveLink(code)
      .then((data) => {
        setLink(data);
        setLoading(false);

        // Track click (fire-and-forget)
        trackClick(code, {
          user_agent: navigator.userAgent,
          referer: document.referrer || undefined,
          device_type: detectDevice(),
        }).catch(() => {});

        // For deeplinks: auto-redirect after brief delay
        if (data.link_type === "deeplink" && data.status === "active") {
          setRedirecting(true);
          const appUri = buildMarketplaceUri(data);
          const webUrl = buildWebUrl(data);

          // Try to open the app; fall back to web after 1.8s
          if (appUri) {
            window.location.href = appUri;
            setTimeout(() => {
              window.location.href = webUrl;
            }, 1800);
          } else {
            setTimeout(() => {
              window.location.href = webUrl;
            }, 500);
          }
        }
      })
      .catch(() => {
        setNotFound(true);
        setLoading(false);
      });
  }, [code]);

  if (loading) {
    return (
      <div className={css.page}>
        <div className={css.card}>
          <div className={css.loading}>Загрузка…</div>
        </div>
      </div>
    );
  }

  if (notFound || !link) {
    return (
      <div className={css.page}>
        <div className={css.card}>
          <div className={css.notFound}>
            <div className={css.notFoundIcon}>🔗</div>
            <div className={css.notFoundTitle}>Ссылка не найдена</div>
            <div className={css.notFoundText}>
              Ссылка устарела или была удалена.
            </div>
          </div>
          <div className={css.poweredBy}>
            Powered by <a href="https://mplays.ru">MPlays</a>
          </div>
        </div>
      </div>
    );
  }

  if (link.status === "paused") {
    return (
      <div className={css.page}>
        <div className={css.card}>
          <div className={css.notFound}>
            <div className={css.notFoundIcon}>⏸</div>
            <div className={css.notFoundTitle}>Ссылка приостановлена</div>
            <div className={css.notFoundText}>
              Эта ссылка временно деактивирована.
            </div>
          </div>
          <div className={css.poweredBy}>
            Powered by <a href="https://mplays.ru">MPlays</a>
          </div>
        </div>
      </div>
    );
  }

  const appUri = buildMarketplaceUri(link);
  const webUrl = buildWebUrl(link);
  const isWb = link.marketplace === "wildberries";

  // Deeplink: show brief redirect notice
  if (link.link_type === "deeplink" && redirecting) {
    return (
      <div className={css.page}>
        <div className={css.card}>
          <div className={css.content}>
            {link.product_image && (
              <div className={css.imgWrap}>
                <img className={css.productImg} src={link.product_image} alt="" />
                <div className={css.marketplaceBadge}>
                  {MARKETPLACE_LABELS[link.marketplace] ?? link.marketplace}
                </div>
              </div>
            )}
            <div className={css.productTitle} style={{ marginTop: 16 }}>
              {link.product_title || "Переход к товару…"}
            </div>
            <div
              style={{
                fontSize: 13,
                color: "#888",
                marginTop: 8,
                marginBottom: 20,
              }}
            >
              Открываем приложение {MARKETPLACE_LABELS[link.marketplace]}…
            </div>

            <a
              href={webUrl}
              className={css.btnWeb}
            >
              Открыть в браузере
            </a>
          </div>
          <div className={css.poweredBy}>
            Powered by <a href="https://mplays.ru">MPlays</a>
          </div>
        </div>
      </div>
    );
  }

  // Autolanding: full product card
  return (
    <div className={css.page}>
      <div className={css.card}>
        {/* Product image */}
        <div className={css.imgWrap}>
          {link.product_image ? (
            <img className={css.productImg} src={link.product_image} alt={link.product_title || ""} />
          ) : (
            <div className={css.imgPlaceholder}>🛍</div>
          )}
          <div className={css.marketplaceBadge}>
            {MARKETPLACE_LABELS[link.marketplace] ?? link.marketplace}
          </div>
        </div>

        {/* Content */}
        <div className={css.content}>
          {link.product_title && (
            <div className={css.productTitle}>{link.product_title}</div>
          )}
          {link.product_price && (
            <div className={css.productPrice}>
              {Number(link.product_price).toLocaleString("ru-RU")} ₽
            </div>
          )}

          {/* Open in app */}
          {appUri && (
            <a
              href={appUri}
              className={`${css.btnApp} ${isWb ? css.btnAppWb : css.btnAppOzon}`}
            >
              <span>📱</span>
              Открыть в приложении {MARKETPLACE_LABELS[link.marketplace]}
            </a>
          )}

          <div className={css.divider}>или</div>

          {/* Open on web */}
          <a href={webUrl} className={css.btnWeb}>
            Перейти на сайт {MARKETPLACE_LABELS[link.marketplace]}
          </a>
        </div>

        <div className={css.poweredBy}>
          Powered by <a href="https://mplays.ru">MPlays</a>
        </div>
      </div>
    </div>
  );
}
