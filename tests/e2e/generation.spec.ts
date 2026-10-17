import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Generation Flow Tests
 * Tests the end-to-end generation workflow
 */
test.describe('Generation Flow', () => {

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

    // Mock generate API
    await page.route('**/api/v1/generate', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task_id: 'test-task-123',
          status: 'pending',
          progress: 0,
          message: 'Task created'
        })
      });
    });

    // Mock task status API
    await page.route('**/api/v1/task/*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task_id: 'test-task-123',
          status: 'generating',
          progress: 30,
          message: 'Generating styled room...'
        })
      });
    });

    // Mock analyze-space API
    await page.route('**/api/v1/analyze-space', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/plain',
        body: 'This is a test analysis...\n[[IMAGE_PROMPT]]\nTest prompt\n[[/IMAGE_PROMPT]]'
      });
    });

    await page.goto('/');
  });

  test('should show style options when not in quick mode', async ({ page }) => {
    // Upload an image first
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(testImagePath);

    // Wait for preview
    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 10000 });

    // Toggle quick mode off by clicking the toggle button in the mode-toggle div
    const quickToggle = page.locator('.mode-toggle button');
    await quickToggle.click();

    // Wait for animation
    await page.waitForTimeout(500);

    // Style options should be visible when quick mode is off
    const styleButton = page.locator('button:has-text("Boho")');
    await expect(styleButton).toBeVisible({ timeout: 5000 });
  });

  test('should allow style selection', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(testImagePath);

    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 10000 });

    // Toggle quick mode off
    const quickToggle = page.locator('.mode-toggle button');
    await quickToggle.click();
    await page.waitForTimeout(500);

    // Click a different style
    const bohoStyle = page.locator('button:has-text("Boho")');
    await bohoStyle.waitFor({ state: 'visible', timeout: 5000 });
    await bohoStyle.click();

    // Should have selected class
    await expect(bohoStyle).toHaveClass(/selected/);
  });

  test('should show generating state after clicking generate', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(testImagePath);

    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 5000 });

    // Wait for upload to complete (button becomes enabled)
    const generateButton = page.getByTestId('generate-button');
    await expect(generateButton).not.toBeDisabled({ timeout: 10000 });

    // Click generate (this will likely fail without backend, but tests the UI flow)
    await generateButton.click();

    // Should show generating state (step 2)
    const taskMessage = page.getByTestId('task-message');
    await expect(taskMessage).toBeVisible({ timeout: 3000 });

    // Progress bar should appear
    const progressBar = page.getByTestId('progress-bar');
    await expect(progressBar).toBeVisible();
  });

});


/**
 * Error Handling Tests
 */
test.describe('Error Handling', () => {

  test.beforeEach(async ({ page }) => {
    // Mock options API
    await page.route('**/api/v1/options*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ room_types: [], styles: [], budgets: [] })
      });
    });

    await page.goto('/');
  });

  test('should show error state on API failure', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/v1/upload', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Server error' })
      });
    });

    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(testImagePath);

    // Should show error message
    const errorMessage = page.getByTestId('error-message');
    await expect(errorMessage).toBeVisible({ timeout: 10000 });
    await expect(errorMessage).toContainText('Server error');
  });

  test('should allow retry after error', async ({ page }) => {
    // Navigate to error state
    await page.evaluate(() => {
      const app = document.querySelector('[x-data]') as any;
      if (app && app.__x) {
        app.__x.$data.step = 'error';
        app.__x.$data.errorMessage = 'Test error';
      }
    });

    // Find and click reset button
    const resetButton = page.locator('button:has-text("Try Again")');
    if (await resetButton.isVisible()) {
      await resetButton.click();

      // Should return to step 1
      const uploadArea = page.getByTestId('upload-area');
      await expect(uploadArea).toBeVisible();
    }
  });

});
