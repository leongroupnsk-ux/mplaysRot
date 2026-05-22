-- ─── Extensions ───────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Users & Auth ─────────────────────────────────────────────────────────────
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'analyst' CHECK (role IN ('owner', 'analyst')),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- ─── Ad Platform Connections ──────────────────────────────────────────────────
CREATE TABLE ad_platform_connections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL CHECK (platform IN (
                        'yandex_direct', 'vk_ads', 'vk_blogger',
                        'telegram_ads', 'messenger_max'
                    )),
    -- Токены хранятся зашифрованными через pgcrypto
    access_token_enc TEXT NOT NULL,
    refresh_token_enc TEXT,
    account_id      TEXT,
    account_name    TEXT,
    token_expires_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, platform, account_id)
);

CREATE INDEX idx_ad_connections_user ON ad_platform_connections(user_id);

-- ─── Marketplace Connections ──────────────────────────────────────────────────
CREATE TABLE marketplace_connections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    marketplace     TEXT NOT NULL CHECK (marketplace IN (
                        'ozon', 'wildberries', 'yandex_market', 'amazon'
                    )),
    api_key_enc     TEXT NOT NULL,
    client_id       TEXT,
    seller_id       TEXT,
    marketplace_name TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, marketplace, client_id)
);

CREATE INDEX idx_mp_connections_user ON marketplace_connections(user_id);

-- ─── Campaigns ────────────────────────────────────────────────────────────────
CREATE TABLE campaigns (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    marketplace     TEXT NOT NULL CHECK (marketplace IN (
                        'ozon', 'wildberries', 'yandex_market', 'amazon'
                    )),
    ad_platform     TEXT NOT NULL CHECK (ad_platform IN (
                        'yandex_direct', 'vk_ads', 'vk_blogger',
                        'telegram_ads', 'messenger_max'
                    )),
    destination_url TEXT NOT NULL,
    budget          NUMERIC(12, 2),
    -- UTM-параметры по умолчанию для генератора ссылок
    utm_source      TEXT,
    utm_medium      TEXT,
    utm_campaign    TEXT,
    -- Внешний ID кампании в рекламном кабинете (если связана)
    external_campaign_id TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_user ON campaigns(user_id);
CREATE INDEX idx_campaigns_platform ON campaigns(ad_platform);
CREATE INDEX idx_campaigns_marketplace ON campaigns(marketplace);

-- ─── Tracking Links ───────────────────────────────────────────────────────────
CREATE TABLE tracking_links (
    trax_id         TEXT PRIMARY KEY,         -- короткий уникальный ID, e.g. "abc123xy"
    campaign_id     UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    destination_url TEXT NOT NULL,
    -- UTM-параметры конкретной ссылки (могут переопределять кампанию)
    utm_source      TEXT,
    utm_medium      TEXT,
    utm_campaign    TEXT,
    utm_content     TEXT,
    utm_term        TEXT,
    label           TEXT,                     -- произвольная метка для различения ссылок
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tracking_links_campaign ON tracking_links(campaign_id);

-- ─── Segment Uploads ──────────────────────────────────────────────────────────
CREATE TABLE segment_uploads (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_id     UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    ad_platform     TEXT NOT NULL,
    lookalike       BOOLEAN NOT NULL DEFAULT FALSE,
    lookalike_scale INT CHECK (lookalike_scale BETWEEN 1 AND 10),
    min_roas_threshold NUMERIC(6, 2) NOT NULL DEFAULT 3.0,
    seed_size       INT,
    -- Статус Celery-задачи
    celery_task_id  TEXT,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
                        'pending', 'processing', 'uploaded', 'failed'
                    )),
    error_message   TEXT,
    -- Внешний ID сегмента в рекламном кабинете после загрузки
    external_segment_id TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_segments_user ON segment_uploads(user_id);
CREATE INDEX idx_segments_campaign ON segment_uploads(campaign_id);
CREATE INDEX idx_segments_status ON segment_uploads(status);

-- ─── Notifications ────────────────────────────────────────────────────────────
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    type        TEXT NOT NULL CHECK (type IN (
                    'anomaly_detected', 'segment_ready',
                    'attribution_complete', 'low_roas', 'budget_depleted'
                )),
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    is_read     BOOLEAN NOT NULL DEFAULT FALSE,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ─── Attribution Window Config ────────────────────────────────────────────────
CREATE TABLE attribution_settings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    marketplace     TEXT NOT NULL,
    window_days     INT NOT NULL DEFAULT 14 CHECK (window_days BETWEEN 1 AND 90),
    method          TEXT NOT NULL DEFAULT 'probabilistic' CHECK (method IN (
                        'strict',       -- только для Ozon/Яндекс.Маркет с UTM
                        'probabilistic' -- ML-модель для WB/Amazon
                    )),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, marketplace)
);

-- ─── Trigger: updated_at ──────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_segments_updated_at
    BEFORE UPDATE ON segment_uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
