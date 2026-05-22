import { http, HttpResponse, delay } from "msw";
import {
  CAMPAIGNS, TRACKING_LINKS, OVERVIEW, TIMESERIES, FUNNEL,
  GEO, TOP_CREATIVES, CLICK_TO_ORDER, ATTRIBUTION_LOG,
  SEGMENTS, NOTIFICATIONS, INTEGRATIONS, STORES, PRODUCTS,
} from "./fixtures";

const BASE = "/api";
const LAG = 300; // ms — имитация сетевой задержки

export const handlers = [

  // ── Auth ───────────────────────────────────────────────────────────────────

  http.post(`${BASE}/v1/auth/login`, async () => {
    await delay(LAG);
    return HttpResponse.json({
      access_token: "mock_access_token",
      refresh_token: "mock_refresh_token",
    });
  }),

  http.post(`${BASE}/v1/auth/register`, async () => {
    await delay(LAG);
    return HttpResponse.json(
      { access_token: "mock_access_token", refresh_token: "mock_refresh_token" },
      { status: 201 }
    );
  }),

  http.get(`${BASE}/v1/auth/me`, async () => {
    await delay(LAG);
    return HttpResponse.json({
      id: "user-0001",
      email: "demo@attribly.io",
      full_name: "Demo Пользователь",
      role: "owner",
      created_at: "2026-01-01T00:00:00Z",
    });
  }),

  http.post(`${BASE}/v1/auth/refresh`, async () => {
    await delay(LAG);
    return HttpResponse.json({
      access_token: "mock_access_token_refreshed",
      refresh_token: "mock_refresh_token_2",
    });
  }),

  http.patch(`${BASE}/v1/auth/me`, async ({ request }) => {
    await delay(LAG);
    const body = await request.json() as Record<string, unknown>;
    if (body.new_password && body.current_password !== "demo123") {
      return HttpResponse.json(
        { detail: "Current password is incorrect" },
        { status: 400 }
      );
    }
    return HttpResponse.json({
      id: "user-0001",
      email: "demo@attribly.io",
      full_name: body.full_name ?? "Demo Пользователь",
      role: "owner",
      created_at: "2026-01-01T00:00:00Z",
    });
  }),

  // ── Campaigns ──────────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/campaigns`, async () => {
    await delay(LAG);
    return HttpResponse.json(CAMPAIGNS);
  }),

  http.get(`${BASE}/v1/campaigns/:id`, async ({ params }) => {
    await delay(LAG);
    const campaign = CAMPAIGNS.find((c) => c.id === params.id);
    if (!campaign) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(campaign);
  }),

  http.post(`${BASE}/v1/campaigns`, async ({ request }) => {
    await delay(LAG);
    const body = await request.json() as Record<string, unknown>;
    const created = {
      id: `c1a2b3c4-${Date.now()}-new`,
      name: String(body.name ?? "Новая кампания"),
      marketplace: body.marketplace ?? "ozon",
      ad_platform: body.ad_platform ?? "vk_ads",
      destination_url: String(body.destination_url ?? ""),
      budget: body.budget ?? null,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(created, { status: 201 });
  }),

  http.patch(`${BASE}/v1/campaigns/:id`, async ({ params, request }) => {
    await delay(LAG);
    const campaign = CAMPAIGNS.find((c) => c.id === params.id);
    if (!campaign) return new HttpResponse(null, { status: 404 });
    const patch = await request.json() as Record<string, unknown>;
    return HttpResponse.json({ ...campaign, ...patch, updated_at: new Date().toISOString() });
  }),

  http.delete(`${BASE}/v1/campaigns/:id`, async ({ params }) => {
    await delay(LAG);
    const exists = CAMPAIGNS.some((c) => c.id === params.id);
    if (!exists) return new HttpResponse(null, { status: 404 });
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE}/v1/campaigns/:id/links`, async ({ params }) => {
    await delay(LAG);
    const links = TRACKING_LINKS[params.id as string] ?? [];
    return HttpResponse.json(links);
  }),

  http.post(`${BASE}/v1/campaigns/:id/links`, async ({ params }) => {
    await delay(LAG);
    const campaign = CAMPAIGNS.find((c) => c.id === params.id);
    if (!campaign) return new HttpResponse(null, { status: 404 });
    const trax_id = Math.random().toString(36).slice(2, 10);
    return HttpResponse.json(
      {
        trax_id,
        tracking_url: `https://t.attribly.io/t/${trax_id}`,
        destination_url: campaign.destination_url,
        label: null,
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  // ── Analytics ──────────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/analytics/overview`, async () => {
    await delay(LAG);
    return HttpResponse.json(OVERVIEW);
  }),

  http.get(`${BASE}/v1/analytics/timeseries`, async () => {
    await delay(LAG);
    return HttpResponse.json(TIMESERIES);
  }),

  http.get(`${BASE}/v1/analytics/funnel`, async () => {
    await delay(LAG);
    return HttpResponse.json(FUNNEL);
  }),

  http.get(`${BASE}/v1/analytics/geo`, async () => {
    await delay(LAG);
    return HttpResponse.json(GEO);
  }),

  http.get(`${BASE}/v1/analytics/top-creatives`, async () => {
    await delay(LAG);
    return HttpResponse.json(TOP_CREATIVES);
  }),

  http.get(`${BASE}/v1/analytics/click-to-order-distribution`, async () => {
    await delay(LAG);
    return HttpResponse.json(CLICK_TO_ORDER);
  }),

  // ── Attribution ────────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/attribution/log`, async ({ request }) => {
    await delay(LAG);
    const url = new URL(request.url);
    const offset = parseInt(url.searchParams.get("offset") ?? "0", 10);
    const limit  = parseInt(url.searchParams.get("limit")  ?? "20", 10);
    return HttpResponse.json({
      ...ATTRIBUTION_LOG,
      items: ATTRIBUTION_LOG.items.slice(offset, offset + limit),
    });
  }),

  // ── Segments ───────────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/segments`, async () => {
    await delay(LAG);
    return HttpResponse.json(SEGMENTS);
  }),

  http.post(`${BASE}/v1/segments/upload`, async ({ request }) => {
    await delay(LAG);
    const body = await request.json() as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: `seg-${Date.now()}`,
        campaign_id: body.campaign_id,
        ad_platform: body.ad_platform,
        lookalike: body.lookalike ?? false,
        lookalike_scale: body.lookalike_scale ?? null,
        min_roas_threshold: body.min_roas_threshold ?? 3.0,
        seed_size: null,
        status: "pending",
        external_segment_id: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      { status: 202 }
    );
  }),

  // ── Notifications ──────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/notifications`, async ({ request }) => {
    await delay(LAG);
    const url = new URL(request.url);
    const unreadOnly = url.searchParams.get("unread_only") === "true";
    const items = unreadOnly
      ? NOTIFICATIONS.filter((n) => !n.is_read)
      : NOTIFICATIONS;
    return HttpResponse.json(items);
  }),

  http.post(`${BASE}/v1/notifications/read-all`, async () => {
    await delay(LAG);
    NOTIFICATIONS.forEach((n) => { n.is_read = true; });
    return HttpResponse.json({ ok: true });
  }),

  http.post(`${BASE}/v1/notifications/:id/read`, async ({ params }) => {
    await delay(LAG);
    const notif = NOTIFICATIONS.find((n) => n.id === params.id);
    if (notif) notif.is_read = true;
    return HttpResponse.json({ ok: true });
  }),

  // ── Reporting ──────────────────────────────────────────────────────────────

  http.post(`/api/reporting/reports/export`, async ({ request }) => {
    await delay(LAG + 400);
    const url = new URL(request.url);
    const type = url.searchParams.get("type") ?? "attribution";
    const dateFrom = url.searchParams.get("date_from") ?? "";
    const dateTo = url.searchParams.get("date_to") ?? "";
    const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const filename = `${type}_${dateFrom}_${dateTo}_${ts}.csv`;
    const fakeUrl = `http://localhost:9010/attribly-reports/reports/mock-user/${filename}?X-Amz-Expires=3600`;
    return HttpResponse.json({
      url: fakeUrl,
      filename,
      rows: Math.floor(Math.random() * 2000) + 50,
      expires_at: new Date(Date.now() + 3_600_000).toISOString(),
    });
  }),

  // ── Integrations ───────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/integrations`, async () => {
    await delay(LAG);
    return HttpResponse.json(INTEGRATIONS);
  }),

  http.post(`${BASE}/v1/integrations/marketplace`, async ({ request }) => {
    await delay(LAG + 200);
    const body = await request.json() as Record<string, unknown>;
    const created = {
      id: `int-${Date.now()}`,
      type: "marketplace" as const,
      provider: String(body.provider ?? "ozon"),
      account_name: String(body.account_name ?? "Новый магазин"),
      status: "active" as const,
      last_synced_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    INTEGRATIONS.push(created);
    return HttpResponse.json(created, { status: 201 });
  }),

  http.post(`${BASE}/v1/integrations/ad`, async ({ request }) => {
    await delay(LAG + 200);
    const body = await request.json() as Record<string, unknown>;
    const created = {
      id: `int-${Date.now()}`,
      type: "ad_platform" as const,
      provider: String(body.provider ?? "vk_ads"),
      account_name: body.account_name ? String(body.account_name) : null,
      status: "active" as const,
      last_synced_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };
    INTEGRATIONS.push(created);
    return HttpResponse.json(created, { status: 201 });
  }),

  http.delete(`${BASE}/v1/integrations/:id`, async ({ params }) => {
    await delay(LAG);
    const idx = INTEGRATIONS.findIndex((i) => i.id === params.id);
    if (idx === -1) return new HttpResponse(null, { status: 404 });
    INTEGRATIONS.splice(idx, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  http.post(`${BASE}/v1/integrations/:id/validate`, async ({ params }) => {
    await delay(LAG + 300);
    const integration = INTEGRATIONS.find((i) => i.id === params.id);
    if (!integration) return new HttpResponse(null, { status: 404 });
    integration.status = "active";
    integration.last_synced_at = new Date().toISOString();
    return HttpResponse.json({ ok: true, message: "Соединение успешно проверено" });
  }),

  // ── Stores ─────────────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/stores`, async () => {
    await delay(LAG);
    return HttpResponse.json(STORES);
  }),

  // ── Products ───────────────────────────────────────────────────────────────

  http.get(`${BASE}/v1/products/search`, async ({ request }) => {
    await delay(LAG);
    const url = new URL(request.url);
    const q = (url.searchParams.get("q") ?? "").toLowerCase();
    const marketplace = url.searchParams.get("marketplace");
    const storeId = url.searchParams.get("store_id");
    const includeOutOfStock = url.searchParams.get("include_out_of_stock") !== "false";
    const expandVariations = url.searchParams.get("expand_variations") !== "false";
    const limit = parseInt(url.searchParams.get("limit") ?? "15", 10);
    const offset = parseInt(url.searchParams.get("offset") ?? "0", 10);

    let items = PRODUCTS.filter((p) => {
      if (marketplace && p.provider !== marketplace) return false;
      if (storeId && p.store_id !== storeId) return false;
      if (!includeOutOfStock && p.stock === 0) return false;
      if (q && !p.title.toLowerCase().includes(q) && !p.external_product_id.toLowerCase().includes(q)) return false;
      return true;
    });

    const total = items.length;
    items = items.slice(offset, offset + limit);

    if (!expandVariations) {
      items = items.map((p) => ({ ...p, variations: [] }));
    }

    return HttpResponse.json({ items, total });
  }),
];
