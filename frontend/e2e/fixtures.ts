/**
 * Shared test fixtures and API mock helpers.
 *
 * All API calls go to /api/v1/* via Vite proxy.  In E2E tests we intercept
 * them with page.route() so no running backend is needed.
 */
import { Page, Route } from "@playwright/test";

// ── Data fixtures ──────────────────────────────────────────────────────────

export const MOCK_USER = {
  id: "user-0001",
  email: "demo@attribly.io",
  full_name: "Demo Пользователь",
  role: "owner",
  created_at: "2026-01-01T00:00:00Z",
};

export const MOCK_TOKENS = {
  access_token: "mock_access_token",
  refresh_token: "mock_refresh_token",
};

export const MOCK_CAMPAIGNS = [
  {
    id: "camp-0001",
    name: "Летняя распродажа",
    marketplace: "ozon",
    ad_platform: "vk_ads",
    destination_url: "https://ozon.ru/product/1",
    budget: 50000,
    is_active: true,
    created_at: "2026-03-01T10:00:00Z",
    updated_at: "2026-03-01T10:00:00Z",
  },
  {
    id: "camp-0002",
    name: "Зимняя акция WB",
    marketplace: "wildberries",
    ad_platform: "yandex_direct",
    destination_url: "https://wb.ru/catalog/1",
    budget: null,
    is_active: false,
    created_at: "2026-02-15T08:30:00Z",
    updated_at: "2026-02-15T08:30:00Z",
  },
];

export const MOCK_NOTIFICATIONS = [
  {
    id: "notif-0001",
    campaign_id: "camp-0001",
    type: "low_roas",
    title: "Низкий ROAS",
    body: "ROAS кампании «Летняя распродажа» упал ниже 3.0",
    is_read: false,
    payload: null,
    created_at: "2026-04-28T12:00:00Z",
  },
];

// ── Route mock helpers ─────────────────────────────────────────────────────

type JsonBody = Record<string, unknown> | unknown[];

function json(page: Page, pattern: string | RegExp, body: JsonBody, status = 200) {
  return page.route(pattern, (route: Route) =>
    route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) })
  );
}

/**
 * Install all standard API mocks. Call at the start of each test that
 * needs a logged-in session with data.
 */
export async function mockApi(page: Page) {
  // Auth
  await json(page, /\/api\/v1\/auth\/me/, MOCK_USER);
  await json(page, /\/api\/v1\/auth\/login/, MOCK_TOKENS);
  await json(page, /\/api\/v1\/auth\/register/, { ...MOCK_TOKENS }, 201);
  await json(page, /\/api\/v1\/auth\/refresh/, {
    access_token: "mock_access_token_2",
    refresh_token: "mock_refresh_token_2",
  });

  // Campaigns
  await page.route(/\/api\/v1\/campaigns\/camp-\w+$/, (route) => {
    const url = route.request().url();
    const id = url.split("/").pop();
    const c = MOCK_CAMPAIGNS.find((x) => x.id === id) ?? MOCK_CAMPAIGNS[0];
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(c) });
  });
  await page.route(/\/api\/v1\/campaigns\/$/, (route) => {
    const method = route.request().method();
    if (method === "POST") {
      const newCamp = {
        ...MOCK_CAMPAIGNS[0],
        id: "camp-9999",
        name: "Тестовая кампания",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(newCamp) });
    } else {
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_CAMPAIGNS) });
    }
  });
  await json(page, /\/api\/v1\/campaigns\/camp-\w+\/links/, []);

  // Notifications
  await json(page, /\/api\/v1\/notifications\//, MOCK_NOTIFICATIONS);
  await json(page, /\/api\/v1\/notifications\/read-all/, { ok: true });

  // Analytics (dashboard)
  await json(page, /\/api\/v1\/analytics\/overview/, {
    revenue: 1250000,
    roas: 4.2,
    spend: 297619,
    clicks: 18500,
    orders: 3200,
    cr: 17.3,
  });
  await json(page, /\/api\/v1\/analytics\/timeseries/, []);
  await json(page, /\/api\/v1\/analytics\/funnel/, []);
  await json(page, /\/api\/v1\/analytics\/geo/, []);
  await json(page, /\/api\/v1\/analytics\/top-creatives/, []);

  // Segments
  await json(page, /\/api\/v1\/segments\//, []);

  // Integrations
  await json(page, /\/api\/v1\/integrations\//, []);

  // Reporting
  await json(page, /\/api\/reporting\/reports\/export/, {
    url: "https://minio.example.com/reports/test.csv?sig=abc",
    filename: "attribution_2026-04-01_2026-04-28.csv",
    rows: 1240,
    expires_at: new Date(Date.now() + 3600_000).toISOString(),
  });
}

/**
 * Seed localStorage so the app thinks the user is already logged in.
 * Must be called before page.goto().
 */
export async function seedAuth(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("access_token", "mock_access_token");
    localStorage.setItem("refresh_token", "mock_refresh_token");
  });
}
