/**
 * E2E: Campaigns flow
 *
 * Covers:
 *  - Campaigns list renders with data
 *  - Empty state renders with CTA
 *  - Create campaign modal opens, fills and submits
 *  - Pause / Resume campaign
 *  - Navigate to campaign detail page
 *  - Edit campaign modal
 */
import { test, expect } from "@playwright/test";
import { mockApi, seedAuth, MOCK_CAMPAIGNS } from "./fixtures";

test.beforeEach(async ({ page }) => {
  await mockApi(page);
  await seedAuth(page);
});

// ── List ───────────────────────────────────────────────────────────────────

test("campaigns page renders both campaigns", async ({ page }) => {
  await page.goto("/campaigns");

  await expect(page.getByText("Летняя распродажа")).toBeVisible();
  await expect(page.getByText("Зимняя акция WB")).toBeVisible();
});

test("campaigns page shows marketplace and platform badges", async ({ page }) => {
  await page.goto("/campaigns");

  await expect(page.getByText("Ozon")).toBeVisible();
  await expect(page.getByText("WB")).toBeVisible();
});

test("active campaign shows green status", async ({ page }) => {
  await page.goto("/campaigns");
  await expect(page.getByText("Активна").first()).toBeVisible();
});

test("paused campaign shows paused status", async ({ page }) => {
  await page.goto("/campaigns");
  await expect(page.getByText("На паузе").first()).toBeVisible();
});

// ── Empty state ────────────────────────────────────────────────────────────

test("empty state shows CTA when no campaigns", async ({ page }) => {
  // Override to return empty list
  await page.route(/\/api\/campaigns\/$/, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: "[]" })
  );

  await page.goto("/campaigns");
  await expect(page.getByText(/нет кампаний/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /создать кампанию/i })).toBeVisible();
});

// ── Create campaign ────────────────────────────────────────────────────────

test("clicking Create opens modal", async ({ page }) => {
  await page.goto("/campaigns");

  await page.getByRole("button", { name: /\+ создать кампанию/i }).first().click();

  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByText(/новая кампания/i)).toBeVisible();
});

test("create campaign form submits and closes modal", async ({ page }) => {
  await page.goto("/campaigns");

  await page.getByRole("button", { name: /\+ создать кампанию/i }).first().click();
  const modal = page.getByRole("dialog");
  await expect(modal).toBeVisible();

  // Fill form
  await modal.getByLabel(/название/i).fill("Тестовая кампания");
  await modal.getByLabel(/маркетплейс/i).selectOption("ozon");
  await modal.getByLabel(/рекламная площадка|площадка/i).selectOption("vk_ads");
  await modal.getByLabel(/url|ссылка/i).fill("https://ozon.ru/product/999");

  // Submit
  await modal.getByRole("button", { name: /создать/i }).click();

  // Modal should close after success
  await expect(modal).not.toBeVisible({ timeout: 5000 });
});

test("create campaign validates required fields", async ({ page }) => {
  await page.goto("/campaigns");
  await page.getByRole("button", { name: /\+ создать кампанию/i }).first().click();

  const modal = page.getByRole("dialog");
  // Try submit without filling anything
  await modal.getByRole("button", { name: /создать/i }).click();

  // Modal stays open — browser validation or our validation fires
  await expect(modal).toBeVisible();
});

// ── Pause / Resume ─────────────────────────────────────────────────────────

test("pause button triggers PATCH request", async ({ page }) => {
  const patchRequests: string[] = [];
  await page.route(/\/api\/campaigns\/camp-\w+$/, (route) => {
    if (route.request().method() === "PATCH") {
      patchRequests.push(route.request().url());
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...MOCK_CAMPAIGNS[0], is_active: false }) });
    } else {
      route.continue();
    }
  });

  await page.goto("/campaigns");
  await page.getByRole("button", { name: /пауза/i }).first().click();

  expect(patchRequests.length).toBeGreaterThan(0);
});

test("resume button triggers PATCH request", async ({ page }) => {
  const patchRequests: string[] = [];
  await page.route(/\/api\/campaigns\/camp-\w+$/, (route) => {
    if (route.request().method() === "PATCH") {
      patchRequests.push(route.request().url());
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...MOCK_CAMPAIGNS[1], is_active: true }) });
    } else {
      route.continue();
    }
  });

  await page.goto("/campaigns");
  await page.getByRole("button", { name: /запустить/i }).first().click();

  expect(patchRequests.length).toBeGreaterThan(0);
});

// ── Navigation to detail ───────────────────────────────────────────────────

test("clicking campaign row navigates to detail page", async ({ page }) => {
  // Mock campaign detail
  await page.route(/\/api\/campaigns\/camp-0001$/, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_CAMPAIGNS[0]) })
  );
  await page.route(/\/api\/analytics\/overview/, (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ revenue: 0, roas: 0, spend: 0, clicks: 0, orders: 0, cr: 0 }) })
  );

  await page.goto("/campaigns");
  // Click the row (not action buttons) — first data row
  await page.locator("tbody tr").first().click();

  await expect(page).toHaveURL(/\/campaigns\/camp-0001/);
});

// ── Edit modal ─────────────────────────────────────────────────────────────

test("edit modal pre-fills campaign name", async ({ page }) => {
  await page.goto("/campaigns");

  await page.getByRole("button", { name: /изменить/i }).first().click();

  const modal = page.getByRole("dialog");
  await expect(modal).toBeVisible();
  // Name field should be pre-filled with existing campaign name
  const nameInput = modal.getByLabel(/название/i);
  await expect(nameInput).toHaveValue("Летняя распродажа");
});

test("edit modal save button triggers PATCH", async ({ page }) => {
  const patchRequests: string[] = [];
  await page.route(/\/api\/campaigns\/camp-\w+$/, (route) => {
    if (route.request().method() === "PATCH") {
      patchRequests.push(route.request().url());
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_CAMPAIGNS[0]) });
    } else {
      route.continue();
    }
  });

  await page.goto("/campaigns");
  await page.getByRole("button", { name: /изменить/i }).first().click();

  const modal = page.getByRole("dialog");
  await modal.getByLabel(/название/i).fill("Новое название");
  await modal.getByRole("button", { name: /сохранить/i }).click();

  await expect(async () => {
    expect(patchRequests.length).toBeGreaterThan(0);
  }).toPass({ timeout: 3000 });
});

// ── Sidebar navigation ─────────────────────────────────────────────────────

test("sidebar contains Кампании link", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("link", { name: "Кампании" })).toBeVisible();
});

test("clicking Кампании in sidebar navigates to /campaigns", async ({ page }) => {
  await page.goto("/dashboard");
  await page.getByRole("link", { name: "Кампании" }).click();
  await expect(page).toHaveURL(/\/campaigns/);
});
