export type AdPlatform =
  | "yandex_direct"
  | "vk_ads"
  | "vk_blogger"
  | "telegram_ads"
  | "messenger_max";

export type Marketplace =
  | "ozon"
  | "wildberries"
  | "yandex_market"
  | "amazon";

export type SegmentStatus = "pending" | "processing" | "uploaded" | "failed";

// ── Analytics ─────────────────────────────────────────────────────────────────
export interface OverviewResponse {
  date_from: string;
  date_to: string;
  total_spend: number;
  total_revenue: number;
  roas: number;
  attributed_orders: number;
  click_to_order_rate: number;
  avg_order_value: number;
  previous_period?: Omit<OverviewResponse, "date_from" | "date_to" | "previous_period">;
}

export interface FunnelStep {
  name: "clicks" | "favorites" | "cart_adds" | "orders";
  count: number;
  conversion_rate: number;
}

export interface FunnelResponse {
  campaign_id: string;
  steps: FunnelStep[];
}

export interface TimeSeriesPoint {
  date: string;
  spend: number;
  revenue: number;
  clicks: number;
  orders: number;
  roas: number;
}

export interface GeoPoint {
  region: string;
  clicks: number;
  orders: number;
  revenue: number;
  conversion_rate: number;
}

export interface TopCreativeRow {
  external_ad_id: string;
  ad_name: string;
  ad_platform: AdPlatform;
  spend: number;
  clicks: number;
  orders: number;
  roas: number;
}

export interface ClickToOrderBucket {
  bucket_label: string;
  count: number;
  pct: number;
}

// ── Campaigns ─────────────────────────────────────────────────────────────────
export interface Campaign {
  id: string;
  name: string;
  marketplace: Marketplace;
  ad_platform: AdPlatform;
  destination_url: string;
  budget: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrackingLink {
  trax_id: string;
  tracking_url: string;
  destination_url: string;
  label: string | null;
  created_at: string;
}

// ── Attribution ───────────────────────────────────────────────────────────────
export interface AttributionLogEntry {
  attribution_id: string;
  order_id: string;
  campaign_id: string;
  trax_id: string;
  marketplace: Marketplace;
  ad_platform: AdPlatform;
  product_id: string;
  order_amount: number;
  click_at: string;
  order_at: string;
  hours_to_order: number;
  confidence: number;
  attribution_method: "strict" | "probabilistic";
  model_version: string;
}

export interface AttributionLogResponse {
  total: number;
  items: AttributionLogEntry[];
}

// ── Segments ──────────────────────────────────────────────────────────────────
export interface SegmentUpload {
  id: string;
  campaign_id: string;
  ad_platform: AdPlatform;
  lookalike: boolean;
  seed_size: number | null;
  status: SegmentStatus;
  external_segment_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// ── Notifications ─────────────────────────────────────────────────────────────
export interface Notification {
  id: string;
  campaign_id: string | null;
  type:
    | "anomaly_detected"
    | "segment_ready"
    | "attribution_complete"
    | "low_roas"
    | "budget_depleted";
  title: string;
  body: string;
  is_read: boolean;
  payload?: Record<string, unknown>;
  created_at: string;
}
