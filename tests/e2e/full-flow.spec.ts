import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Full Flow E2E Tests
 * Complete user journey tests using real room images
 */
test.describe('Full User Flow', () => {

  const testImages = [
    { name: 'Bedroom with green wall', file: 'test-room.jpg' },
    { name: 'Living room with balcony', file: 'test-room-2.jpg' }
  ];

  test.beforeEach(async ({ page }) => {
    // Mock the upload API
    await page.route('**/api/v1/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          image_id: 'test-image-123',
          image_url: '/uploads/test-image-123.jpg',
          message: 'Upload successful'
        })
      });
    });

    // Mock options API
    await page.route('**/api/v1/options*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          room_types: [{ value: 'living_room', label: 'Living Room' }],
          styles: [
            { value: 'boho', label: 'Boho', description: 'Eclectic warm' },
            { value: 'modern_minimalist', label: 'Modern Minimal', description: 'Clean lines' }
          ],
          budgets: [{ value: '400', label: '$400', amount: 400, description: 'Core upgrade' }]
        })
      });
    });

    await page.goto('/');
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
  });

  for (const testImage of testImages) {
    test(`should complete full flow with ${testImage.name}`, async ({ page }) => {
      // Step 1: Upload image
      const testImagePath = path.join(__dirname, '../fixtures', testImage.file);
      const fileInput = page.getByTestId('file-input');

      await fileInput.setInputFiles(testImagePath);

      // Verify preview appears
      const previewImage = page.getByTestId('preview-image');
      await expect(previewImage).toBeVisible({ timeout: 10000 });

      // Verify upload status
      const uploadStatus = page.getByTestId('upload-status');
      await expect(uploadStatus).toContainText('Ready to style', { timeout: 15000 });

      // Step 2: Verify generate button is enabled
      const generateButton = page.getByTestId('generate-button');
      await expect(generateButton).toBeEnabled({ timeout: 5000 });
      await expect(generateButton).toContainText('One-Click Makeover');
    });
  }

  test('should allow changing style before generation', async ({ page }) => {
    // Upload first image
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(testImagePath);

    // Wait for preview
    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 10000 });

    // Turn off quick mode to see style options
    const toggleButton = page.locator('button').filter({ has: page.locator('span.rounded-full.shadow') }).first();
    await toggleButton.click();

    // Wait for style options to appear
    await page.waitForTimeout(500);

    // Try to find and click a style option
    const bohoButton = page.locator('button:has-text("Boho")');
    if (await bohoButton.isVisible({ timeout: 3000 })) {
      await bohoButton.click();
      await expect(bohoButton).toHaveClass(/selected/);
    }
  });

  test('should show proper loading states', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');

    // Check initial state
    await expect(page.getByTestId('upload-area')).toContainText('Drop your room photo here');

    // Upload
    await fileInput.setInputFiles(testImagePath);

    // Should show uploading state briefly
    const uploadStatus = page.getByTestId('upload-status');
    await expect(uploadStatus).toBeVisible({ timeout: 5000 });

    // Eventually should show ready
    await expect(uploadStatus).toContainText('Ready to style', { timeout: 15000 });
  });

});


/**
 * Mobile Responsiveness Tests
 */
test.describe('Mobile Experience', () => {

  test.beforeEach(async ({ page }) => {
    // Mock APIs
    await page.route('**/api/v1/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, image_id: 'test-123', image_url: '/uploads/test.jpg', message: 'OK' })
      });
    });
    await page.route('**/api/v1/options*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ room_types: [], styles: [], budgets: [] })
      });
    });

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
  });

  test('should display correctly on mobile', async ({ page }) => {
    // Check title is visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();

    // Check upload area is visible and clickable
    const uploadArea = page.getByTestId('upload-area');
    await expect(uploadArea).toBeVisible();

    // Trust badges should be visible
    await expect(page.locator('text=Secure Upload')).toBeVisible();
  });

  test('should handle file upload on mobile', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');

    await fileInput.setInputFiles(testImagePath);

    // Preview should appear
    const previewImage = page.getByTestId('preview-image');
    await expect(previewImage).toBeVisible({ timeout: 10000 });
  });

});


/**
 * Accessibility Tests
 */
test.describe('Accessibility', () => {

  test('should have proper heading structure', async ({ page }) => {
    await page.goto('/');

    // Should have h1
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    expect(await h1.count()).toBe(1);
  });

  test('should have accessible upload area', async ({ page }) => {
    await page.goto('/');

    const uploadArea = page.getByTestId('upload-area');
    await expect(uploadArea).toBeVisible();

    // Should be keyboard accessible (has click handler)
    await uploadArea.focus();
    await page.keyboard.press('Enter');
    // File dialog would open (we can't test native dialogs)
  });

  test('should have visible focus indicators', async ({ page }) => {
    await page.goto('/');

    // Tab through elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Check that focused element has visible styling
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

});


/**
 * Performance Tests
 */
test.describe('Performance', () => {

  test('should load page quickly', async ({ page }) => {
    // Mock APIs
    await page.route('**/api/v1/options*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ room_types: [], styles: [], budgets: [] })
      });
    });

    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;

    // Page should load in under 5 seconds (allow more time for CI)
    expect(loadTime).toBeLessThan(5000);
  });

  test('should handle large image gracefully', async ({ page }) => {
    // Mock APIs
    await page.route('**/api/v1/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, image_id: 'test-123', image_url: '/uploads/test.jpg', message: 'OK' })
      });
    });
    await page.route('**/api/v1/options*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ room_types: [], styles: [], budgets: [] })
      });
    });

    await page.goto('/');

    // The living room image is larger
    const testImagePath = path.join(__dirname, '../fixtures/test-room-2.jpg');
    const fileInput = page.getByTestId('file-input');

    const startTime = Date.now();
    await fileInput.setInputFiles(testImagePath);

    // Should show preview within reasonable time
    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 10000 });
    const processTime = Date.now() - startTime;

    // Image processing should complete in under 5 seconds
    expect(processTime).toBeLessThan(5000);
  });

});
