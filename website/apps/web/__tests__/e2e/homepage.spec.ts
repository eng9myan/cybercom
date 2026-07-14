import { test, expect } from "@playwright/test";

test.describe("Homepage", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/en");
  });

  test("has correct title", async ({ page }) => {
    await expect(page).toHaveTitle(/CyberCom/);
  });

  test("renders hero section", async ({ page }) => {
    const heading = page.getByRole("heading", { level: 1 });
    await expect(heading).toBeVisible();
    await expect(heading).toContainText("Transforming");
  });

  test("renders navigation", async ({ page }) => {
    const nav = page.getByRole("banner");
    await expect(nav).toBeVisible();
  });

  test("has working demo CTA button", async ({ page }) => {
    const demoBtn = page.getByRole("link", { name: /request a demo/i }).first();
    await expect(demoBtn).toBeVisible();
    await demoBtn.click();
    await expect(page).toHaveURL(/\/demo/);
  });

  test("product ecosystem section is visible", async ({ page }) => {
    await page.getByText("CyberCom Ecosystem").scrollIntoViewIfNeeded();
    await expect(page.getByRole("heading", { name: /cybercom ecosystem/i })).toBeVisible();
  });

  test("CyMed section exists", async ({ page }) => {
    await page.getByText("CyMed").first().scrollIntoViewIfNeeded();
    await expect(page.getByText("Healthcare Platform").first()).toBeVisible();
  });

  test("footer has newsletter form", async ({ page }) => {
    const footer = page.getByRole("contentinfo");
    const emailInput = footer.getByRole("textbox");
    await expect(emailInput).toBeVisible();
  });
});

test.describe("Accessibility", () => {
  test("has skip to main content link", async ({ page }) => {
    await page.goto("/en");
    const skipLink = page.getByText(/skip to main content/i);
    await expect(skipLink).toBeHidden(); // Hidden until focused
    await skipLink.focus();
    await expect(skipLink).toBeVisible();
  });

  test("all images have alt text", async ({ page }) => {
    await page.goto("/en");
    const images = await page.locator("img").all();
    for (const img of images) {
      const alt = await img.getAttribute("alt");
      expect(alt).not.toBeNull();
    }
  });
});

test.describe("Arabic (RTL) layout", () => {
  test("renders Arabic page with RTL direction", async ({ page }) => {
    await page.goto("/ar");
    const html = page.locator("html");
    await expect(html).toHaveAttribute("dir", "rtl");
    await expect(html).toHaveAttribute("lang", "ar");
  });
});

test.describe("Navigation", () => {
  test("navigates to products page", async ({ page }) => {
    await page.goto("/en");
    await page.getByRole("navigation").getByText("Products").click();
    // Mega menu should appear or navigate
  });

  test("navigates to industries page", async ({ page }) => {
    await page.goto("/en");
    await page.getByRole("link", { name: "Industries" }).click();
    await expect(page).toHaveURL(/\/industries/);
  });
});
