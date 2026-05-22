-- Blog platform tables
-- Run once against the PostgreSQL database

CREATE TABLE IF NOT EXISTS blog_articles (
    id            BIGSERIAL PRIMARY KEY,
    title         VARCHAR(255)  NOT NULL,
    slug          VARCHAR(255)  NOT NULL UNIQUE,
    excerpt       TEXT,
    content       TEXT,
    cover_image   VARCHAR(500),
    category      VARCHAR(50)   NOT NULL DEFAULT 'general',
    tags          TEXT[]        NOT NULL DEFAULT '{}',
    author        VARCHAR(100)  NOT NULL DEFAULT 'Команда Attribly',
    published_at  TIMESTAMPTZ,
    status        VARCHAR(16)   NOT NULL DEFAULT 'draft',
    view_count    INTEGER       NOT NULL DEFAULT 0,
    like_count    INTEGER       NOT NULL DEFAULT 0,
    meta_title    VARCHAR(70),
    meta_description VARCHAR(160),
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blog_articles_slug     ON blog_articles (slug);
CREATE INDEX IF NOT EXISTS idx_blog_articles_status   ON blog_articles (status);
CREATE INDEX IF NOT EXISTS idx_blog_articles_category ON blog_articles (category);

CREATE TABLE IF NOT EXISTS blog_views (
    id              BIGSERIAL PRIMARY KEY,
    article_id      BIGINT      NOT NULL REFERENCES blog_articles(id) ON DELETE CASCADE,
    ip_hash         VARCHAR(64) NOT NULL,
    user_agent_hash VARCHAR(64) NOT NULL DEFAULT '',
    viewed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blog_views_article ON blog_views (article_id);
CREATE INDEX IF NOT EXISTS idx_blog_views_ip      ON blog_views (article_id, ip_hash);

CREATE TABLE IF NOT EXISTS blog_likes (
    id          BIGSERIAL PRIMARY KEY,
    article_id  BIGINT      NOT NULL REFERENCES blog_articles(id) ON DELETE CASCADE,
    ip_hash     VARCHAR(64) NOT NULL,
    cookie_id   VARCHAR(64),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (article_id, ip_hash)
);

CREATE INDEX IF NOT EXISTS idx_blog_likes_article ON blog_likes (article_id);
