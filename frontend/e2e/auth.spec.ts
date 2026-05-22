/**
 * E2E: Auth flow
 *
 * Covers:
 *  - Login page renders and submits credentials
 *  - Successful login → redirect to /dashboard
 *  - Wrong credentials → error message
 *  - Register page submits and redirects
 *  - Logout clears session and returns to /login
 *  - Protected routes redirect unauthenticated users to /login
 */
import { test, expect } from "@playwright/test";
import { mockApi, seedAuth, MOCK_USER } from "./fixtures";

// ── Login ──────────────────────────────────────────────────────────────────

test("login page renders form fields", async ({ page }) => {
  await mockApi(page);
  await page.goto("/login");

  await expect(page.getByLabel(/email/i)).toBeVisible();
  await expect(page.getByLabel(/пароль/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /войти/i })).toBeVisible();
});

test("successful login redirects to dashboard", async ({ page }) => {
  await mockApi(page);
  await page.goto("/login");

  await page.getByLabel(/email/i).fill("demo@attribly.io");
  await page.getByLabel(/пароль/i).fill("demo123");
  await page.getByRole("button", { name: /войти/i }).click();

  await expect(page).toHaveURL(/\/dashboard/);
});

test("login saves tokens to localStorage", async ({ page }) => {
  await mockApi(page);
  await page.goto("/login");

  await page.getByLabel(/email/i).fill("demo@attribly.io");
  await page.getByLabel(/пароль/i).fill("demo123");
  await page.getByRole("button", { name: /войти/i }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  const token = await page.evaluate(() => localStorage.getItem("access_token"));
  expect(token).toBe("mock_access_token");
});

test("wrong credentials show error message", async ({ page }) => {
  // Override login to return 401
  await page.route(/\/api\/auth\/login/, (route) =>
    route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Invalid credentials" }) })
  );
  await mockApi(page);
  await page.goto("/login");

  await page.getByLabel(/email/i).fill("wrong@example.com");
  await page.getByLabel(/пароль/i).fill("badpass");
  await page.getByRole("button", { name: /войти/i }).click();

  await expect(page.getByText(/неверный email или пароль/i)).toBeVisible();
  await expect(page).toHaveURL(/\/login/);
});

test("submit button is disabled while loading", async ({ page }) => {
  // Slow API so we can catch the loading state
  await page.route(/\/api\/auth\/login/, async (route) => {
    await new Promise((r) => setTimeout(r, 2000));
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ access_token: "t", refresh_token: "r" }) });
  });
  await mockApi(page);
  await page.goto("/login");

  await page.getByLabel(/email/i).fill("demo@attribly.io");
  await page.getByLabel(/пароль/i).fill("demo123");

  const btn = page.getByRole("button", { name: /войти/i });
  await btn.click();
  await expect(btn).toBeDisabled();
});

test("login page has register link", async ({ page }) => {
  await mockApi(page);
  await page.goto("/login");
  await expect(page.getByRole("link", { name: /регистрация|зарегистрироваться/i })).toBeVisible();
});

// ── Register ───────────────────────────────────────────────────────────────

test("register page renders form fields", async ({ page }) => {
  await mockApi(page);
  await page.goto("/register");

  await expect(page.getByLabel(/email/i)).toBeVisible();
  await expect(page.getByLabel(/пароль/i).first()).toBeVisible();
});

test("successful register redirects to dashboard", async ({ page }) => {
  await mockApi(page);
  await page.goto("/register");

  await page.getByLabel(/email/i).fill("new@attribly.io");
  // Fill password — might be multiple fields, take first
  const passwordFields = page.getByLabel(/пароль/i);
  await passwordFields.first().fill("securepass123");
  await page.getByRole("button", { name: /зарегистрироваться|создать/i }).click();

  await expect(page).toHaveURL(/\/dashboard/);
});

test("register shows error for short password", async ({ page }) => {
  await mockApi(page);
  await page.goto("/register");

  await page.getByLabel(/email/i).fill("short@example.com");
  await page.getByLabel(/пароль/i).first().fill("short");
  await page.getByRole("button", { name: /зарегистрироваться|создать/i }).click();

  await expect(page.getByText(/не менее 8/i)).toBeVisible();
  await expect(page).toHaveURL(/\/register/);
});

// ── Logout ─────────────────────────────────────────────────────────────────

test("logout clears session and redirects to login", async ({ page }) => {
  await mockApi(page);
  await seedAuth(page);
  await page.goto("/dashboard");

  // Wait for sidebar to appear
  await expect(page.getByText(MOCK_USER.full_name)).toBeVisible();

  // Click logout button (↩ symbol)
  await page.getByTitle(/выйти/i).click();

  await expect(page).toHaveURL(/\/login/);
  const token = await page.evaluate(() => localStorage.getItem("access_token"));
  expect(token).toBeNull();
});

// ── Protected routes ────────────────────────────────────────────────────────

test("unauthenticated user is redirected from dashboard to login", async ({ page }) => {
  await mockApi(page);
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login/);
});

test("unauthenticated user is redirected from campaigns to login", async ({ page }) => {
  await mockApi(page);
  await page.goto("/campaigns");
  await expect(page).toHaveURL(/\/login/);
});

test("authenticated user can access dashboard", async ({ page }) => {
  await mockApi(page);
  await seedAuth(page);
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/dashboard/);
});
