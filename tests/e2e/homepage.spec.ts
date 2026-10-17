import { test, expect } from '@playwright/test';

/**
 * Homepage Tests
 * Tests the landing page and basic UI elements
 */
test.describe('Homepage', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display the main heading', async ({ page }) => {
    // Check main title is visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('One photo');
    await expect(heading).toContainText('Instant makeover');
  });

  test('should display Makeover Camera branding', async ({ page }) => {
    const brand = page.locator('text=Makeover Camera');
    await expect(brand.first()).toBeVisible();
  });

  test('should show upload area', async ({ page }) => {
    const uploadArea = page.getByTestId('upload-area');
    await expect(uploadArea).toBeVisible();
    await expect(uploadArea).toContainText('Drop your room photo here');
  });

  test('should have quick mode toggle', async ({ page }) => {
    const quickToggle = page.locator('text=Quick');
    await expect(quickToggle).toBeVisible();
  });

  test('should show trust badges', async ({ page }) => {
    await expect(page.locator('text=Secure Upload')).toBeVisible();
    await expect(page.locator('text=Results in ~30s')).toBeVisible();
    await expect(page.locator('text=Shop Direct')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    const uploadArea = page.getByTestId('upload-area');
    await expect(uploadArea).toBeVisible();
  });

});
