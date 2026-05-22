import type {
  Campaign, TrackingLink, OverviewResponse, TimeSeriesPoint,
  FunnelResponse, GeoPoint, TopCreativeRow, ClickToOrderBucket,
  AttributionLogEntry, AttributionLogResponse, SegmentUpload, Notification,
} from "../api/types";
import type { Integration } from "../api/integrations";
import type { Store } from "../api/stores";
import type { Product } from "../api/products";

// ── Campaigns ─────────────────────────────────────────────────────────────────

export const CAMPAIGNS: Campaign[] = [
  {
    id: "c1a2b3c4-0001-0001-0001-000000000001",
    name: "VK Ads → Ozon | Лето 2026",
    marketplace: "ozon",
    ad_platform: "vk_ads",
    destination_url: "https://ozon.ru/product/12345678",
    budget: 150000,
    is_active: true,
    created_at: "2026-04-01T10:00:00Z",
    updated_at: "2026-04-20T08:30:00Z",
  },
  {
    id: "c1a2b3c4-0002-0002-0002-000000000002",
    name: "Яндекс.Директ → WB | Кроссовки",
    marketplace: "wildberries",
    ad_platform: "yandex_direct",
    destination_url: "https://wildberries.ru/catalog/98765432/detail.aspx",
    budget: 80000,
    is_active: true,
    created_at: "2026-04-05T12:00:00Z",
    updated_at: "2026-04-25T14:10:00Z",
  },
  {
    id: "c1a2b3c4-0003-0003-0003-000000000003",
    name: "Telegram Ads → ЯМ | Электроника",
    marketplace: "yandex_market",
    ad_platform: "telegram_ads",
    destination_url: "https://market.yandex.ru/product/55443322",
    budget: 50000,
    is_active: false,
    created_at: "2026-03-15T09:00:00Z",
    updated_at: "2026-04-10T11:00:00Z",
  },
];

export const TRACKING_LINKS: Record<string, TrackingLink[]> = {
  "c1a2b3c4-0001-0001-0001-000000000001": [
    {
      trax_id: "ab12cd34",
      tracking_url: "https://t.attribly.io/t/ab12cd34",
      destination_url: "https://ozon.ru/product/12345678?utm_source=vk_ads&utm_medium=cpc&trax_id=ab12cd34",
      label: "default",
      created_at: "2026-04-01T10:01:00Z",
    },
    {
      trax_id: "ef56gh78",
      tracking_url: "https://t.attribly.io/t/ef56gh78",
      destination_url: "https://ozon.ru/product/12345678?utm_source=vk_ads&utm_medium=cpc&utm_content=banner_v2&trax_id=ef56gh78",
      label: "banner_v2",
      created_at: "2026-04-10T15:30:00Z",
    },
  ],
  "c1a2b3c4-0002-0002-0002-000000000002": [
    {
      trax_id: "ij90kl12",
      tracking_url: "https://t.attribly.io/t/ij90kl12",
      destination_url: "https://wildberries.ru/catalog/98765432/detail.aspx?utm_source=yandex_direct&trax_id=ij90kl12",
      label: "default",
      created_at: "2026-04-05T12:01:00Z",
    },
  ],
};

// ── Analytics ─────────────────────────────────────────────────────────────────

export const OVERVIEW: OverviewResponse = {
  date_from: "2026-04-01",
  date_to: "2026-04-28",
  total_spend: 187430,
  total_revenue: 1124580,
  roas: 5.99,
  attributed_orders: 843,
  click_to_order_rate: 0.0412,
  avg_order_value: 1334.02,
  previous_period: {
    total_spend: 164200,
    total_revenue: 918400,
    roas: 5.59,
    attributed_orders: 701,
    click_to_order_rate: 0.0378,
    avg_order_value: 1310.13,
  },
};

function makeDay(date: string, spend: number, roas: number, clicks: number): TimeSeriesPoint {
  const revenue = Math.round(spend * roas);
  const orders = Math.round(clicks * 0.042);
  return { date, spend, revenue, clicks, orders, roas };
}

export const TIMESERIES: TimeSeriesPoint[] = [
  makeDay("2026-04-01", 5800, 5.4, 1820),
  makeDay("2026-04-02", 6100, 5.6, 1950),
  makeDay("2026-04-03", 5500, 5.2, 1700),
  makeDay("2026-04-04", 7200, 6.1, 2300),
  makeDay("2026-04-05", 6800, 5.9, 2100),
  makeDay("2026-04-06", 7400, 6.3, 2450),
  makeDay("2026-04-07", 8100, 6.8, 2700),
  makeDay("2026-04-08", 7600, 6.5, 2500),
  makeDay("2026-04-09", 6900, 6.0, 2200),
  makeDay("2026-04-10", 7100, 6.2, 2350),
  makeDay("2026-04-11", 7800, 6.6, 2600),
  makeDay("2026-04-12", 8300, 7.0, 2850),
  makeDay("2026-04-13", 8700, 7.3, 3000),
  makeDay("2026-04-14", 9200, 7.8, 3200),
  makeDay("2026-04-15", 6100, 5.5, 1900),
  makeDay("2026-04-16", 6400, 5.7, 2000),
  makeDay("2026-04-17", 7000, 6.1, 2250),
  makeDay("2026-04-18", 7500, 6.4, 2480),
  makeDay("2026-04-19", 8000, 6.9, 2700),
  makeDay("2026-04-20", 8500, 7.2, 2900),
  makeDay("2026-04-21", 9100, 7.7, 3100),
  makeDay("2026-04-22", 9600, 8.1, 3300),
  makeDay("2026-04-23", 7200, 6.3, 2300),
  makeDay("2026-04-24", 7700, 6.6, 2550),
  makeDay("2026-04-25", 8200, 7.0, 2800),
  makeDay("2026-04-26", 8800, 7.5, 3050),
  makeDay("2026-04-27", 9300, 7.9, 3250),
  makeDay("2026-04-28", 4600, 6.2, 1500),
];

export const FUNNEL: FunnelResponse = {
  campaign_id: "c1a2b3c4-0001-0001-0001-000000000001",
  steps: [
    { name: "clicks",    count: 20480, conversion_rate: 1.0 },
    { name: "favorites", count: 4096,  conversion_rate: 0.2 },
    { name: "cart_adds", count: 1638,  conversion_rate: 0.4 },
    { name: "orders",    count: 843,   conversion_rate: 0.515 },
  ],
};

export const GEO: GeoPoint[] = [
  { region: "Москва",          clicks: 8200,  orders: 310, revenue: 421800, conversion_rate: 0.0378 },
  { region: "Санкт-Петербург", clicks: 4100,  orders: 172, revenue: 233680, conversion_rate: 0.042  },
  { region: "Новосибирск",     clicks: 1800,  orders: 65,  revenue: 88400,  conversion_rate: 0.036  },
  { region: "Екатеринбург",    clicks: 1540,  orders: 58,  revenue: 78860,  conversion_rate: 0.0377 },
  { region: "Казань",          clicks: 1200,  orders: 44,  revenue: 59840,  conversion_rate: 0.0367 },
  { region: "Нижний Новгород", clicks: 980,   orders: 34,  revenue: 46240,  conversion_rate: 0.0347 },
  { region: "Краснодар",       clicks: 860,   orders: 31,  revenue: 42140,  conversion_rate: 0.0360 },
  { region: "Самара",          clicks: 720,   orders: 26,  revenue: 35360,  conversion_rate: 0.0361 },
  { region: "Ростов-на-Дону",  clicks: 640,   orders: 21,  revenue: 28560,  conversion_rate: 0.0328 },
  { region: "Омск",            clicks: 440,   orders: 14,  revenue: 19040,  conversion_rate: 0.0318 },
];

export const TOP_CREATIVES: TopCreativeRow[] = [
  { external_ad_id: "ad_001", ad_name: "Баннер 600×400 | Кеды белые",   ad_platform: "vk_ads",       spend: 38200, clicks: 12400, orders: 312, roas: 10.9 },
  { external_ad_id: "ad_002", ad_name: "Карусель | Летняя коллекция",    ad_platform: "vk_ads",       spend: 29800, clicks: 9600,  orders: 241, roas: 8.6  },
  { external_ad_id: "ad_003", ad_name: "РСЯ | Кроссовки скидка 30%",     ad_platform: "yandex_direct", spend: 24600, clicks: 7800,  orders: 187, roas: 7.4  },
  { external_ad_id: "ad_004", ad_name: "Поиск | кроссовки купить",       ad_platform: "yandex_direct", spend: 18900, clicks: 5200,  orders: 143, roas: 6.9  },
  { external_ad_id: "ad_005", ad_name: "Telegram | Скидки недели",       ad_platform: "telegram_ads",  spend: 14200, clicks: 3900,  orders: 89,  roas: 5.8  },
  { external_ad_id: "ad_006", ad_name: "VK Reels | Обзор кед",           ad_platform: "vk_blogger",    spend: 11800, clicks: 3200,  orders: 71,  roas: 5.1  },
];

export const CLICK_TO_ORDER: ClickToOrderBucket[] = [
  { bucket_label: "< 1 ч",   count: 184, pct: 21.8 },
  { bucket_label: "1–6 ч",   count: 227, pct: 26.9 },
  { bucket_label: "6–24 ч",  count: 196, pct: 23.3 },
  { bucket_label: "1–3 дня", count: 142, pct: 16.8 },
  { bucket_label: "3–7 дней",count: 68,  pct: 8.1  },
  { bucket_label: "> 7 дней",count: 26,  pct: 3.1  },
];

// ── Attribution log ────────────────────────────────────────────────────────────

const ATTR_ITEMS: AttributionLogEntry[] = Array.from({ length: 20 }, (_, i) => ({
  attribution_id: `attr-${String(i + 1).padStart(4, "0")}`,
  order_id:       `order-${String(10000 + i)}`,
  campaign_id:    i % 3 === 2
    ? "c1a2b3c4-0003-0003-0003-000000000003"
    : i % 2 === 0
      ? "c1a2b3c4-0001-0001-0001-000000000001"
      : "c1a2b3c4-0002-0002-0002-000000000002",
  trax_id:        ["ab12cd34", "ef56gh78", "ij90kl12"][i % 3],
  marketplace:    (["ozon", "wildberries", "yandex_market"] as const)[i % 3],
  ad_platform:    (["vk_ads", "yandex_direct", "telegram_ads"] as const)[i % 3],
  product_id:     `prod-${String(1000 + i)}`,
  order_amount:   Math.round(800 + Math.random() * 3200),
  click_at:       `2026-04-${String(15 + (i % 13)).padStart(2, "0")}T${String(8 + (i % 12)).padStart(2, "0")}:${String(i * 3 % 60).padStart(2, "0")}:00Z`,
  order_at:       `2026-04-${String(16 + (i % 12)).padStart(2, "0")}T${String(10 + (i % 10)).padStart(2, "0")}:00:00Z`,
  hours_to_order: +(1 + i * 2.4).toFixed(1),
  confidence:     i % 3 === 0 ? 1.0 : +(0.62 + (i % 8) * 0.04).toFixed(2),
  attribution_method: i % 3 === 0 ? "strict" : "probabilistic",
  model_version:  i % 3 === 0 ? "utm_join_v1" : "catboost_v1",
}));

export const ATTRIBUTION_LOG: AttributionLogResponse = {
  total: 843,
  items: ATTR_ITEMS,
};

// ── Segments ──────────────────────────────────────────────────────────────────

export const SEGMENTS: SegmentUpload[] = [
  {
    id: "seg-0001",
    campaign_id: "c1a2b3c4-0001-0001-0001-000000000001",
    ad_platform: "vk_ads",
    lookalike: true,
    seed_size: 312,
    status: "uploaded",
    external_segment_id: "vk_seg_9912345",
    error_message: null,
    created_at: "2026-04-20T09:00:00Z",
    updated_at: "2026-04-20T09:45:00Z",
  },
  {
    id: "seg-0002",
    campaign_id: "c1a2b3c4-0002-0002-0002-000000000002",
    ad_platform: "yandex_direct",
    lookalike: false,
    seed_size: 187,
    status: "processing",
    external_segment_id: null,
    error_message: null,
    created_at: "2026-04-28T08:00:00Z",
    updated_at: "2026-04-28T08:10:00Z",
  },
  {
    id: "seg-0003",
    campaign_id: "c1a2b3c4-0003-0003-0003-000000000003",
    ad_platform: "telegram_ads",
    lookalike: true,
    seed_size: 89,
    status: "failed",
    external_segment_id: null,
    error_message: "Seed size too small (min 100 required by platform)",
    created_at: "2026-04-15T14:00:00Z",
    updated_at: "2026-04-15T14:05:00Z",
  },
];

// ── Notifications ─────────────────────────────────────────────────────────────

export const NOTIFICATIONS: Notification[] = [
  {
    id: "notif-001",
    campaign_id: "c1a2b3c4-0001-0001-0001-000000000001",
    type: "anomaly_detected",
    title: "Аномалия в кампании «VK Ads → Ozon | Лето 2026»",
    body: "Метрика CTR отклонилась на 42% от нормы. Текущее значение: 0.8%, ожидалось: 1.4%.",
    is_read: false,
    payload: { metric: "ctr", current: 0.008, expected: 0.014, deviation_pct: 42, severity: "warning" },
    created_at: "2026-04-28T07:30:00Z",
  },
  {
    id: "notif-002",
    campaign_id: "c1a2b3c4-0001-0001-0001-000000000001",
    type: "segment_ready",
    title: "Look-alike сегмент загружен",
    body: "Сегмент из 312 покупателей загружен в VK Ads. Похожая аудитория: ~28 000 человек.",
    is_read: false,
    payload: { segment_id: "seg-0001", seed_size: 312, lookalike_size: 28000 },
    created_at: "2026-04-20T09:45:00Z",
  },
  {
    id: "notif-003",
    campaign_id: "c1a2b3c4-0002-0002-0002-000000000002",
    type: "low_roas",
    title: "ROAS ниже порога в кампании «Яндекс.Директ → WB»",
    body: "ROAS за последние 7 дней: 2.8. Порог: 3.0.",
    is_read: true,
    payload: { roas: 2.8, threshold: 3.0 },
    created_at: "2026-04-22T12:00:00Z",
  },
];

// ── Integrations ──────────────────────────────────────────────────────────────

export let INTEGRATIONS: Integration[] = [
  {
    id: "int-001",
    type: "marketplace",
    provider: "ozon",
    account_name: "ИП Иванов",
    status: "active",
    last_synced_at: "2026-04-28T06:00:00Z",
    created_at: "2026-04-01T10:00:00Z",
  },
  {
    id: "int-002",
    type: "marketplace",
    provider: "wildberries",
    account_name: "ООО Ромашка",
    status: "active",
    last_synced_at: "2026-04-28T07:00:00Z",
    created_at: "2026-04-05T12:00:00Z",
  },
  {
    id: "int-003",
    type: "ad_platform",
    provider: "vk_ads",
    account_name: "VK Кабинет #12345",
    status: "active",
    last_synced_at: "2026-04-28T08:00:00Z",
    created_at: "2026-04-01T11:00:00Z",
  },
  {
    id: "int-004",
    type: "ad_platform",
    provider: "yandex_direct",
    account_name: "Директ Агентство",
    status: "error",
    last_synced_at: "2026-04-25T10:00:00Z",
    created_at: "2026-04-05T13:00:00Z",
  },
];

// ── Stores ────────────────────────────────────────────────────────────────────

export const STORES: Store[] = [
  {
    id: "store-001",
    connection_id: "conn-001",
    provider: "ozon",
    external_store_id: "ozon-seller-00112233",
    name: "ИП Иванов — Ozon",
    logo_url: null,
    is_active: true,
    last_sync_at: "2026-04-28T06:00:00Z",
    created_at: "2026-04-01T10:05:00Z",
  },
  {
    id: "store-002",
    connection_id: "conn-002",
    provider: "wildberries",
    external_store_id: "wb-seller-44556677",
    name: "ООО Ромашка — WB",
    logo_url: null,
    is_active: true,
    last_sync_at: "2026-04-28T07:00:00Z",
    created_at: "2026-04-05T12:05:00Z",
  },
];

// ── Products ──────────────────────────────────────────────────────────────────

export const PRODUCTS: Product[] = [
  {
    id: "prod-001",
    store_id: "store-001",
    provider: "ozon",
    external_product_id: "OZ-123456",
    parent_external_id: null,
    title: "Кроссовки беговые «Спринт Pro» — мужские",
    price: 4990,
    stock: 38,
    image_url: "https://picsum.photos/seed/prod001/64/64",
    has_variations: true,
    is_active: true,
    is_archived: false,
    variations: [
      { external_product_id: "OZ-123456-42", title: "Размер 42", stock: 12 },
      { external_product_id: "OZ-123456-43", title: "Размер 43", stock: 20 },
      { external_product_id: "OZ-123456-44", title: "Размер 44", stock: 6 },
    ],
  },
  {
    id: "prod-002",
    store_id: "store-001",
    provider: "ozon",
    external_product_id: "OZ-789012",
    parent_external_id: null,
    title: "Футболка спортивная «AirCool» — унисекс",
    price: 1290,
    stock: 0,
    image_url: "https://picsum.photos/seed/prod002/64/64",
    has_variations: false,
    is_active: true,
    is_archived: false,
    variations: [],
  },
  {
    id: "prod-003",
    store_id: "store-001",
    provider: "ozon",
    external_product_id: "OZ-345678",
    parent_external_id: null,
    title: "Рюкзак «TrekLight 25L» — туристический",
    price: 3450,
    stock: 15,
    image_url: "https://picsum.photos/seed/prod003/64/64",
    has_variations: true,
    is_active: true,
    is_archived: false,
    variations: [
      { external_product_id: "OZ-345678-BLK", title: "Чёрный", stock: 8 },
      { external_product_id: "OZ-345678-GRN", title: "Зелёный", stock: 7 },
    ],
  },
  {
    id: "prod-004",
    store_id: "store-002",
    provider: "wildberries",
    external_product_id: "WB-98765432",
    parent_external_id: null,
    title: "Носки спортивные компрессионные 3 пары",
    price: 690,
    stock: 201,
    image_url: "https://picsum.photos/seed/prod004/64/64",
    has_variations: false,
    is_active: true,
    is_archived: false,
    variations: [],
  },
  {
    id: "prod-005",
    store_id: "store-002",
    provider: "wildberries",
    external_product_id: "WB-11223344",
    parent_external_id: null,
    title: "Гантели разборные 2×10 кг",
    price: 5990,
    stock: 4,
    image_url: "https://picsum.photos/seed/prod005/64/64",
    has_variations: true,
    is_active: true,
    is_archived: false,
    variations: [
      { external_product_id: "WB-11223344-A", title: "Хром", stock: 2 },
      { external_product_id: "WB-11223344-B", title: "Чёрные", stock: 2 },
    ],
  },
];
