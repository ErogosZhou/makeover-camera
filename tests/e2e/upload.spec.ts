import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Upload Tests
 * Tests the image upload functionality
 */
test.describe('Image Upload', () => {

  test.beforeEach(async ({ page }) => {
    // Mock the upload API to simulate successful upload
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
          styles: [{ value: 'modern_minimalist', label: 'Modern Minimal', description: 'Clean lines' }],
          budgets: [{ value: '400', label: '$400', amount: 400, description: 'Core upgrade' }]
        })
      });
    });

    await page.goto('/');
  });

  test('should open file picker when clicking upload area', async ({ page }) => {
    const uploadArea = page.getByTestId('upload-area');
    const fileInput = page.getByTestId('file-input');

    // File input should be hidden
    await expect(fileInput).toBeHidden();

    // Click should trigger file input
    await uploadArea.click();
    // We can't fully test the native file picker, but we verify the structure is correct
    await expect(fileInput).toHaveAttribute('accept', 'image/jpeg,image/png,image/webp');
  });

  test('should show preview after file selection', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');

    // Upload via file input
    const fileInput = page.getByTestId('file-input');
    await fileInput.setInputFiles(testImagePath);

    // Preview should appear
    const previewImage = page.getByTestId('preview-image');
    await expect(previewImage).toBeVisible({ timeout: 10000 });

    // Upload status should show "Ready to style!" after mock API returns
    const uploadStatus = page.getByTestId('upload-status');
    await expect(uploadStatus).toBeVisible({ timeout: 10000 });
    await expect(uploadStatus).toContainText('Ready to style', { timeout: 10000 });
  });

  test('should show generate button after upload', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');

    await fileInput.setInputFiles(testImagePath);

    // Wait for preview
    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 10000 });

    // Wait for upload to complete (mocked)
    await page.waitForTimeout(500);

    // Generate button should appear and be visible
    const generateButton = page.getByTestId('generate-button');
    await expect(generateButton).toBeVisible({ timeout: 5000 });
  });

  test('should enable generate button after successful upload', async ({ page }) => {
    const testImagePath = path.join(__dirname, '../fixtures/test-room.jpg');
    const fileInput = page.getByTestId('file-input');

    await fileInput.setInputFiles(testImagePath);

    // Wait for preview and upload
    await page.getByTestId('preview-image').waitFor({ state: 'visible', timeout: 10000 });

    // Wait for upload status to show ready
    await expect(page.getByTestId('upload-status')).toContainText('Ready to style', { timeout: 10000 });

    // Generate button should be enabled
    const generateButton = page.getByTestId('generate-button');
    await expect(generateButton).toBeEnabled({ timeout: 5000 });
  });

});
