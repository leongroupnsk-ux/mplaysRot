-- ============================================================
-- LinkEngine: deep_links, link_clicks, custom_domains
-- Run once on a fresh DB or apply as a migration.
-- ============================================================

-- Custom domains (must exist before deep_links references it)
CREATE TABLE IF NOT EXISTS custom_domains (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain          VARCHAR(253) NOT NULL UNIQUE,
    domain_type     VARCHAR(16)  NOT NULL DEFAULT 'own',   -- own | purchased
    status          VARCHAR(24)  NOT NULL DEFAULT 'pending_cname',
    -- pending_cname | pending_ssl | active | error | suspended
    cname_verified  BOOLEAN      NOT NULL DEFAULT FALSE,
    ssl_type        VARCHAR(32),          -- letsencrypt | sectigo
    ssl_expires_at  TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_custom_domains_user_id ON custom_domains(user_id);
CREATE INDEX IF NOT EXISTS ix_custom_domains_status  ON custom_domains(status);

-- Deep links
CREATE TABLE IF NOT EXISTS deep_links (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID    NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id            UUID    NOT NULL,
    -- Denormalised product info (resilient to catalog changes)
    marketplace         VARCHAR(32) NOT NULL,             -- wildberries | ozon
    external_product_id TEXT        NOT NULL,             -- nm_id / product_id
    product_title       TEXT,
    product_image       TEXT,
    product_price       VARCHAR(32),
    -- Link config
    link_type           VARCHAR(16)  NOT NULL DEFAULT 'deeplink', -- deeplink | autolanding
    short_code          VARCHAR(16)  NOT NULL UNIQUE,
    -- UTM params
    utm_source          TEXT,
    utm_medium          TEXT,
    utm_campaign        TEXT,
    utm_term            TEXT,
    utm_content         TEXT,
    -- Custom domain (optional)
    custom_domain_id    UUID REFERENCES custom_domains(id) ON DELETE SET NULL,
    -- State
    status              VARCHAR(24) NOT NULL DEFAULT 'active',
    -- active | paused | product_unavailable
    click_count         INTEGER     NOT NULL DEFAULT 0,
    name                TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_deep_links_user_id    ON deep_links(user_id);
CREATE INDEX IF NOT EXISTS ix_deep_links_short_code ON deep_links(short_code);
CREATE INDEX IF NOT EXISTS ix_deep_links_store_id   ON deep_links(store_id);

-- Click tracking
CREATE TABLE IF NOT EXISTS link_clicks (
    id            BIGSERIAL   PRIMARY KEY,
    deep_link_id  UUID        NOT NULL REFERENCES deep_links(id) ON DELETE CASCADE,
    ip_hash       VARCHAR(64) NOT NULL,
    user_agent    TEXT,
    device_type   VARCHAR(16),      -- mobile | desktop | tablet
    referer       TEXT,
    clicked_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_link_clicks_deep_link_id ON link_clicks(deep_link_id);
CREATE INDEX IF NOT EXISTS ix_link_clicks_clicked_at   ON link_clicks(clicked_at);

-- ── Trigger: auto-update updated_at ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_deep_links_updated_at'
    ) THEN
        CREATE TRIGGER trg_deep_links_updated_at
        BEFORE UPDATE ON deep_links
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_custom_domains_updated_at'
    ) THEN
        CREATE TRIGGER trg_custom_domains_updated_at
        BEFORE UPDATE ON custom_domains
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END
$$;
