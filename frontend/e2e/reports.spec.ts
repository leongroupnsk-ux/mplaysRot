/**
 * E2E: Reports page
 *
 * Covers:
 *  - Reports page renders all 3 report cards
 *  - Clicking export triggers POST to reporting service
 *  - Export history row appears after successful export
 *  - DateRangePicker is present on the page
 *  - Download link is present in history
 *  - Error banner appears when export fails
 *  - Loading state on export button during request
 */
import { test, expect } from "@playwright/test";
import { mockApi, seedAuth } from "./fixtures";

const EXPORT_RESPONSE = {
  url: "https://minio.example.com/reports/attribution_2026-04-28.csv?sig=abc123",
  filename: "attribution_2026-04-01_2026-04-28.csv",
  rows: 1240,
  expires_at: new Date(Date.now() + 3600_000).toISOString(),
};

test.beforeEach(async ({ page }) => {
  await mockApi(page);
  await seedAuth(page);
});

// ── Page structure ─────────────────────────────────────────────────────────

test("reports page renders heading", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByRole("heading", { name: /отчёты/i })).toBeVisible();
});

test("reports page shows attribution card", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByText("Атрибуция")).toBeVisible();
});

test("reports page shows overview card", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByText("Сводка по дням")).toBeVisible();
});

test("reports page shows campaigns card", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByText("По кампаниям")).toBeVisible();
});

test("each report card has export button", async ({ page }) => {
  await page.goto("/reports");
  const exportButtons = page.getByRole("button", { name: /↓ csv/i });
  await expect(exportButtons).toHaveCount(3);
});

test("date range picker is visible", async ({ page }) => {
  await page.goto("/reports");
  // DateRangePicker renders date inputs or selectors
  await expect(page.locator("input[type='date']").first()).toBeVisible();
});

// ── Export flow ────────────────────────────────────────────────────────────

test("clicking export sends POST to reporting service", async ({ page }) => {
  const exportRequests: string[] = [];
  await page.route(/\/api\/reporting\/reports\/export/, (route) => {
    exportRequests.push(route.request().url());
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPORT_RESPONSE),
    });
  });

  await page.goto("/reports");
  await page.getByRole("button", { name: /↓ csv/i }).first().click();

  await expect(async () => {
    expect(exportRequests.length).toBe(1);
  }).toPass({ timeout: 5000 });
});

test("export button shows loading state during request", async ({ page }) => {
  await page.route(/\/api\/reporting\/reports\/export/, async (route) => {
    await new Promise((r) => setTimeout(r, 1500));
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPORT_RESPONSE),
    });
  });

  await page.goto("/reports");
  const btn = page.getByRole("button", { name: /↓ csv/i }).first();
  await btn.click();

  await expect(btn).toHaveText(/генерация/i);
  await expect(btn).toBeDisabled();
});

test("export history row appears after success", async ({ page }) => {
  await page.route(/\/api\/reporting\/reports\/export/, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPORT_RESPONSE),
    })
  );

  await page.goto("/reports");
  await page.getByRole("button", { name: /↓ csv/i }).first().click();

  // History section should appear with the filename
  await expect(page.getByText("История экспортов")).toBeVisible({ timeout: 5000 });
  await expect(page.getByText(EXPORT_RESPONSE.filename)).toBeVisible();
});

test("export history shows row count", async ({ page }) => {
  await page.route(/\/api\/reporting\/reports\/export/, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPORT_RESPONSE),
    })
  );

  await page.goto("/reports");
  await page.getByRole("button", { name: /↓ csv/i }).first().click();

  await expect(page.getByText(/1\s*240\s*строк/i)).toBeVisible({ timeout: 5000 });
});

test("export history shows download link", async ({ page }) => {
  await page.route(/\/api\/reporting\/reports\/export/, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPORT_RESPONSE),
    })
  );

  await page.goto("/reports");
  await page.getByRole("button", { name: /↓ csv/i }).first().click();

  await expect(page.getByRole("link", { name: /скачать/i })).toBeVisible({ timeout: 5000 });
});

test("multiple exports accumulate in history", async ({ page }) => {
  let counter = 0;
  await page.route(/\/api\/reporting\/reports\/export/, (route) => {
    counter++;
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ...EXPORT_RESPONSE,
        filename: `report_${counter}.csv`,
      }),
    });
  });

  await page.goto("/reports");
  const btns = page.getByRole("button", { name: /↓ csv/i });

  await btns.nth(0).click();
  await page.waitForTimeout(500);
  await btns.nth(1).click();
  await page.waitForTimeout(500);

  const downloadLinks = page.getByRole("link", { name: /скачать/i });
  await expect(downloadLinks).toHaveCount(2, { timeout: 5000 });
});

// ── Error handling ─────────────────────────────────────────────────────────

test("error banner appears when export fails", async ({ page }) => {
  await page.route(/\/api\/reporting\/reports\/export/, (route) =>
    route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: "Server error" }) })
  );

  await page.goto("/reports");
  await page.getByRole("button", { name: /↓ csv/i }).first().click();

  await expect(page.getByText(/не удалось сформировать отчёт/i)).toBeVisible({ timeout: 5000 });
});

test("export button re-enables after error", async ({ page }) => {
  await page.route(/\/api\/reporting\/reports\/export/, (route) =>
    route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ detail: "Error" }) })
  );

  await page.goto("/reports");
  const btn = page.getByRole("button", { name: /↓ csv/i }).first();
  await btn.click();

  // After error, button should be clickable again
  await expect(btn).not.toBeDisabled({ timeout: 5000 });
});

// ── Sidebar ────────────────────────────────────────────────────────────────

test("sidebar contains Отчёты link", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.getByRole("link", { name: "Отчёты" })).toBeVisible();
});

test("clicking Отчёты navigates to /reports", async ({ page }) => {
  await page.goto("/dashboard");
  await page.getByRole("link", { name: "Отчёты" }).click();
  await expect(page).toHaveURL(/\/reports/);
});
