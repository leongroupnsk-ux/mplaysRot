import api from "./client";
import adminApi from "./admin";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DeepLink {
  id: string;
  user_id: string;
  store_id: string;
  marketplace: string;
  external_product_id: string;
  product_title: string | null;
  product_image: string | null;
  product_price: string | null;
  link_type: "deeplink" | "autolanding";
  short_code: string;
  name: string | null;
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  utm_term: string | null;
  utm_content: string | null;
  custom_domain_id: string | null;
  status: "active" | "paused" | "product_unavailable";
  click_count: number;
  created_at: string;
  updated_at: string;
}

export interface DeepLinkPublic {
  id: string;
  marketplace: string;
  external_product_id: string;
  product_title: string | null;
  product_image: string | null;
  product_price: string | null;
  link_type: "deeplink" | "autolanding";
  short_code: string;
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  status: string;
}

export interface DeepLinkCreate {
  store_id: string;
  marketplace: string;
  external_product_id: string;
  product_title?: string;
  product_image?: string;
  product_price?: string;
  link_type?: "deeplink" | "autolanding";
  name?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  custom_domain_id?: string;
}

export interface DeepLinkUpdate {
  name?: string;
  status?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

export interface VerifySkuResponse {
  valid: boolean;
  product_title?: string | null;
  product_image?: string | null;
  product_price?: string | null;
  message?: string | null;
}

export interface ClickTrackRequest {
  user_agent?: string;
  referer?: string;
  device_type?: string;
}

// ── CustomDomain ─────────────────────────────────────────────────────────────

export interface CustomDomain {
  id: string;
  user_id: string;
  domain: string;
  domain_type: "own" | "purchased";
  status: "pending_cname" | "pending_ssl" | "active" | "error" | "suspended";
  cname_verified: boolean;
  ssl_type: string | null;
  ssl_expires_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface CustomDomainCreate {
  domain: string;
  domain_type?: "own" | "purchased";
}

export interface CnameTarget {
  cname: string;
  ttl: number;
}

// ── Deep links API ────────────────────────────────────────────────────────────

export const fetchLinks = (params?: { marketplace?: string; link_type?: string }) =>
  api.get<DeepLink[]>("/links", { params }).then((r) => r.data);

export const createLink = (payload: DeepLinkCreate) =>
  api.post<DeepLink>("/links", payload).then((r) => r.data);

export const getLink = (id: string) =>
  api.get<DeepLink>(`/links/${id}`).then((r) => r.data);

export const updateLink = (id: string, payload: DeepLinkUpdate) =>
  api.patch<DeepLink>(`/links/${id}`, payload).then((r) => r.data);

export const deleteLink = (id: string) =>
  api.delete(`/links/${id}`);

export const verifySkuApi = (store_id: string, external_product_id: string) =>
  api
    .get<VerifySkuResponse>("/links/verify-sku", { params: { store_id, external_product_id } })
    .then((r) => r.data);

// ── Link stats ────────────────────────────────────────────────────────────────

export interface DailyStat { date: string; clicks: number }
export interface FunnelStage { stage: string; value: number | null; note: string }
export interface SourceStat { source: string; clicks: number }

export interface LinkStats {
  link: {
    id: string; name: string | null; short_code: string;
    external_product_id: string; product_title: string | null;
    product_image: string | null; marketplace: string;
    utm_source: string | null; utm_medium: string | null;
    utm_campaign: string | null; status: string; created_at: string;
  };
  summary: {
    total_clicks: number; unique_visitors: number;
    orders: number; conversion_rate: number; days: number;
  };
  daily: DailyStat[];
  devices: Record<string, number>;
  sources: SourceStat[];
  funnel: FunnelStage[];
}

export const fetchLinkStats = (id: string, days = 30) =>
  api.get<LinkStats>(`/links/${id}/stats`, { params: { days } }).then((r) => r.data);

// Public resolve (no auth)
export const resolveLink = (short_code: string) =>
  api.get<DeepLinkPublic>(`/links/resolve/${short_code}`).then((r) => r.data);

export const trackClick = (short_code: string, payload: ClickTrackRequest) =>
  api.post(`/links/resolve/${short_code}/click`, payload);

// ── Domains API ───────────────────────────────────────────────────────────────

export const fetchDomains = () =>
  api.get<CustomDomain[]>("/domains").then((r) => r.data);

export const addDomain = (payload: CustomDomainCreate) =>
  api.post<CustomDomain>("/domains", payload).then((r) => r.data);

export const deleteDomain = (id: string) =>
  api.delete(`/domains/${id}`);

export const fetchCnameTarget = () =>
  api.get<CnameTarget>("/domains/cname-target").then((r) => r.data);

// ── Admin domains API ─────────────────────────────────────────────────────────

export const adminFetchDomains = (params?: { status?: string; domain_type?: string }) =>
  adminApi.get<CustomDomain[]>("/domains", { params }).then((r) => r.data);

export const adminVerifyDomain = (id: string) =>
  adminApi.post<CustomDomain>(`/domains/${id}/verify`).then((r) => r.data);

export const adminActivateDomain = (id: string) =>
  adminApi.post<CustomDomain>(`/domains/${id}/activate`).then((r) => r.data);

export const adminSuspendDomain = (id: string) =>
  adminApi.post<CustomDomain>(`/domains/${id}/suspend`).then((r) => r.data);

export const adminDeleteDomain = (id: string) =>
  adminApi.delete(`/domains/${id}`);

/** Build a full short URL for a given link using custom domain or system domain. */
export function buildShortUrl(link: DeepLink, domainMap?: Record<string, CustomDomain>): string {
  const systemBase = "https://attribly.ru/l";
  if (link.custom_domain_id && domainMap?.[link.custom_domain_id]) {
    const d = domainMap[link.custom_domain_id];
    if (d.status === "active") {
      return `https://${d.domain}/${link.short_code}`;
    }
  }
  return `${systemBase}/${link.short_code}`;
}

/** Build marketplace deep link URI. */
export function buildMarketplaceUri(link: DeepLinkPublic): string {
  if (link.marketplace === "wildberries") {
    return `wildberries://product-detail?nm_id=${link.external_product_id}`;
  }
  if (link.marketplace === "ozon") {
    return `ozon://products/${link.external_product_id}/`;
  }
  return "";
}

/** Build marketplace web fallback URL. */
export function buildWebUrl(link: DeepLinkPublic): string {
  const utmParams = new URLSearchParams();
  if (link.utm_source) utmParams.set("utm_source", link.utm_source);
  if (link.utm_medium) utmParams.set("utm_medium", link.utm_medium);
  if (link.utm_campaign) utmParams.set("utm_campaign", link.utm_campaign);
  const qs = utmParams.toString() ? `?${utmParams.toString()}` : "";

  if (link.marketplace === "wildberries") {
    return `https://www.wildberries.ru/catalog/${link.external_product_id}/detail.aspx${qs}`;
  }
  if (link.marketplace === "ozon") {
    return `https://www.ozon.ru/product/${link.external_product_id}/${qs}`;
  }
  return "";
}
