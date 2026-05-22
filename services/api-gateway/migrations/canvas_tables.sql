-- ============================================================
-- Attribly Canvas: canvas_boards, board_widgets,
--                  board_connections, board_templates
-- ============================================================

-- Templates (reference table, seeded below)
CREATE TABLE IF NOT EXISTS board_templates (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(255) NOT NULL,
    description      TEXT,
    category         VARCHAR(64)  NOT NULL,  -- pnl_sku | brand_rollout | traffic_analysis | logistics | competitor
    thumbnail_emoji  VARCHAR(8)   NOT NULL DEFAULT '📋',
    template_data    JSONB        NOT NULL DEFAULT '{}',
    is_system        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Canvas boards
CREATE TABLE IF NOT EXISTS canvas_boards (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL DEFAULT 'Новый канвас',
    description     TEXT,
    template_id     UUID         REFERENCES board_templates(id) ON DELETE SET NULL,
    is_public       BOOLEAN      NOT NULL DEFAULT FALSE,
    share_token     VARCHAR(64)  UNIQUE,
    -- Persisted viewport (restore last position)
    viewport_x      FLOAT        NOT NULL DEFAULT 0,
    viewport_y      FLOAT        NOT NULL DEFAULT 0,
    viewport_zoom   FLOAT        NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_canvas_boards_user_id ON canvas_boards(user_id);

-- Widgets on a board
CREATE TABLE IF NOT EXISTS board_widgets (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id     UUID        NOT NULL REFERENCES canvas_boards(id) ON DELETE CASCADE,
    -- product_card | logistics | ad_connector | mini_chart | sticker | text | kpi_table
    widget_type  VARCHAR(32) NOT NULL,
    -- World-space position
    x            FLOAT       NOT NULL DEFAULT 0,
    y            FLOAT       NOT NULL DEFAULT 0,
    width        FLOAT       NOT NULL DEFAULT 300,
    height       FLOAT       NOT NULL DEFAULT 200,
    z_index      INTEGER     NOT NULL DEFAULT 0,
    -- Widget-specific data (store_id, sku, campaign_id, content, color…)
    data         JSONB       NOT NULL DEFAULT '{}',
    -- Visual style overrides (locked, bg_color, border_color…)
    style        JSONB       NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_board_widgets_board_id ON board_widgets(board_id);

-- Connections between widgets
CREATE TABLE IF NOT EXISTS board_connections (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id       UUID        NOT NULL REFERENCES canvas_boards(id) ON DELETE CASCADE,
    from_widget_id UUID        NOT NULL REFERENCES board_widgets(id) ON DELETE CASCADE,
    to_widget_id   UUID        NOT NULL REFERENCES board_widgets(id) ON DELETE CASCADE,
    -- {type: solid|dashed, color: #B0C4DE, thickness: 2}
    style          JSONB       NOT NULL DEFAULT '{}',
    label          VARCHAR(255),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_board_connections_board_id ON board_connections(board_id);

-- Auto-update updated_at (reuse function from links migration if it exists)
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_canvas_boards_updated_at') THEN
        CREATE TRIGGER trg_canvas_boards_updated_at
        BEFORE UPDATE ON canvas_boards
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_board_widgets_updated_at') THEN
        CREATE TRIGGER trg_board_widgets_updated_at
        BEFORE UPDATE ON board_widgets
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;

-- ── Seed templates ────────────────────────────────────────────────────────────

INSERT INTO board_templates (name, description, category, thumbnail_emoji, template_data)
VALUES
(
    'P&L одного SKU',
    'Карточка товара, график изменения маржинальности и заметки о затратах.',
    'pnl_sku',
    '💰',
    '{
        "widgets": [
            {"id":"t1","type":"product_card","x":60,"y":80,"width":280,"height":360,"data":{},"style":{},"z_index":0},
            {"id":"t2","type":"sticker","x":380,"y":80,"width":240,"height":140,"data":{"content":"💡 P&L Анализ\n\nВыручка: \nСебестоимость: \nКомиссия WB: \nРеклама: \n─────────\nМаржа: ","color":"#FFF3D6"},"style":{},"z_index":0},
            {"id":"t3","type":"mini_chart","x":380,"y":260,"width":340,"height":180,"data":{"metric":"sales","period":"30d"},"style":{},"z_index":0},
            {"id":"t4","type":"sticker","x":60,"y":480,"width":660,"height":100,"data":{"content":"📝 Заметки по затратам на логистику и рекламу...","color":"#E6F0FA"},"style":{},"z_index":0}
        ],
        "connections": [
            {"from_widget_id":"t1","to_widget_id":"t3","style":{"type":"solid","color":"#B0C4DE","thickness":2}}
        ]
    }'
),
(
    'Brand Rollout Roadmap',
    'Пошаговая дорожная карта для вывода нового бренда на несколько маркетплейсов.',
    'brand_rollout',
    '🚀',
    '{
        "widgets": [
            {"id":"t1","type":"sticker","x":60,"y":60,"width":200,"height":120,"data":{"content":"✅ Шаг 1\nРегистрация бренда\nна маркетплейсе","color":"#d1fae5"},"style":{},"z_index":0},
            {"id":"t2","type":"sticker","x":300,"y":60,"width":200,"height":120,"data":{"content":"📦 Шаг 2\nЗапуск карточки\nтовара","color":"#FFF3D6"},"style":{},"z_index":0},
            {"id":"t3","type":"sticker","x":540,"y":60,"width":200,"height":120,"data":{"content":"📢 Шаг 3\nЗапуск первых\nрекламных кампаний","color":"#E6F0FA"},"style":{},"z_index":0},
            {"id":"t4","type":"sticker","x":780,"y":60,"width":200,"height":120,"data":{"content":"📊 Шаг 4\nАнализ результатов\nи оптимизация","color":"#fce7f3"},"style":{},"z_index":0},
            {"id":"t5","type":"product_card","x":300,"y":240,"width":280,"height":360,"data":{},"style":{},"z_index":0},
            {"id":"t6","type":"ad_connector","x":640,"y":240,"width":260,"height":200,"data":{},"style":{},"z_index":0}
        ],
        "connections": [
            {"from_widget_id":"t1","to_widget_id":"t2","style":{"type":"solid","color":"#B0C4DE","thickness":2}},
            {"from_widget_id":"t2","to_widget_id":"t3","style":{"type":"solid","color":"#B0C4DE","thickness":2}},
            {"from_widget_id":"t3","to_widget_id":"t4","style":{"type":"solid","color":"#B0C4DE","thickness":2}},
            {"from_widget_id":"t5","to_widget_id":"t6","style":{"type":"dashed","color":"#B0C4DE","thickness":1}}
        ]
    }'
),
(
    'Анализ внешнего трафика',
    'Рекламные коннекторы, связанные с карточками товаров. Выделение лучших каналов по ROMI.',
    'traffic_analysis',
    '📡',
    '{
        "widgets": [
            {"id":"t1","type":"ad_connector","x":60,"y":120,"width":260,"height":200,"data":{"label":"Яндекс.Директ"},"style":{},"z_index":0},
            {"id":"t2","type":"ad_connector","x":60,"y":360,"width":260,"height":200,"data":{"label":"VK Реклама"},"style":{},"z_index":0},
            {"id":"t3","type":"product_card","x":400,"y":200,"width":280,"height":360,"data":{},"style":{},"z_index":0},
            {"id":"t4","type":"mini_chart","x":720,"y":120,"width":340,"height":200,"data":{"metric":"romi","period":"7d"},"style":{},"z_index":0},
            {"id":"t5","type":"sticker","x":720,"y":360,"width":260,"height":160,"data":{"content":"🏆 Лучший канал:\n\nROMI: \nCPC: \nRASHOD:","color":"#d1fae5"},"style":{},"z_index":0}
        ],
        "connections": [
            {"from_widget_id":"t1","to_widget_id":"t3","style":{"type":"solid","color":"#9b59b6","thickness":2}},
            {"from_widget_id":"t2","to_widget_id":"t3","style":{"type":"solid","color":"#3498db","thickness":2}},
            {"from_widget_id":"t3","to_widget_id":"t4","style":{"type":"dashed","color":"#B0C4DE","thickness":1}}
        ]
    }'
),
(
    'План пополнения складов',
    'Логистические виджеты по всем складам с прогнозом спроса.',
    'logistics',
    '📦',
    '{
        "widgets": [
            {"id":"t1","type":"logistics","x":60,"y":80,"width":260,"height":220,"data":{"warehouse":"Коледино"},"style":{},"z_index":0},
            {"id":"t2","type":"logistics","x":360,"y":80,"width":260,"height":220,"data":{"warehouse":"Подольск"},"style":{},"z_index":0},
            {"id":"t3","type":"logistics","x":660,"y":80,"width":260,"height":220,"data":{"warehouse":"Казань"},"style":{},"z_index":0},
            {"id":"t4","type":"mini_chart","x":60,"y":360,"width":860,"height":180,"data":{"metric":"stock","period":"30d"},"style":{},"z_index":0},
            {"id":"t5","type":"sticker","x":60,"y":580,"width":560,"height":120,"data":{"content":"📋 Задача на пополнение:\n\nТовар:\nКол-во:\nСклад назначения:\nДата отправки:","color":"#FFF3D6"},"style":{},"z_index":0}
        ],
        "connections": []
    }'
),
(
    'Конкурентный анализ',
    'Доска для сравнения конкурентов: цены, рейтинг, позиции.',
    'competitor',
    '🔍',
    '{
        "widgets": [
            {"id":"t1","type":"product_card","x":60,"y":80,"width":280,"height":360,"data":{"label":"Мой товар"},"style":{"border_color":"#22c55e","border_width":2},"z_index":0},
            {"id":"t2","type":"sticker","x":400,"y":80,"width":260,"height":180,"data":{"content":"🥊 Конкурент 1\n\nЦена: \nРейтинг: ★\nОтзывы: \nПозиция: ","color":"#fee2e2"},"style":{},"z_index":0},
            {"id":"t3","type":"sticker","x":400,"y":300,"width":260,"height":180,"data":{"content":"🥊 Конкурент 2\n\nЦена: \nРейтинг: ★\nОтзывы: \nПозиция: ","color":"#fef3c7"},"style":{},"z_index":0},
            {"id":"t4","type":"sticker","x":720,"y":80,"width":260,"height":400,"data":{"content":"📊 Выводы\n\n✅ Наши преимущества:\n\n⚠️ Слабые места:\n\n🎯 Действия:\n","color":"#E6F0FA"},"style":{},"z_index":0}
        ],
        "connections": []
    }'
)
ON CONFLICT DO NOTHING;
