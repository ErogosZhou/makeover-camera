import { test, expect } from '@playwright/test';

/**
 * Results Page Tests
 * Tests the results/shopping list display
 */
test.describe('Results Display', () => {

  const mockResult = {
    task_id: 'test-123',
    generated_image_url: '/uploads/test-generated.jpg',
    original_image_url: '/uploads/test-original.jpg',
    shopping_list: [
      {
        identified_item: {
          id: 'item_1',
          name: 'Modern Floor Lamp',
          category: 'Lighting',
          description: 'Sleek modern floor lamp with brass finish',
          price_estimate: '$80-120',
          search_keywords: ['floor lamp', 'modern lamp', 'brass lamp']
        },
        matched_products: [
          {
            id: 'prod_1',
            name: 'Brass Arc Floor Lamp',
            price: 89.99,
            image_url: 'https://example.com/lamp.jpg',
            affiliate_link: 'https://amazon.com/lamp',
            platform: 'Amazon'
          }
        ]
      },
      {
        identified_item: {
          id: 'item_2',
          name: 'Woven Area Rug',
          category: 'Textiles',
          description: 'Natural fiber woven rug',
          price_estimate: '$150-250',
          search_keywords: ['area rug', 'woven rug']
        },
        matched_products: []
      }
    ],
    total_estimated_price: 89.99,
    space_analysis: 'This is a modern living room with good natural light.'
  };

  test('should display results page correctly', async ({ page }) => {
    await page.goto('/');

    // Inject mock data and navigate to results
    await page.evaluate((result) => {
      // Access Alpine.js data
      const appEl = document.querySelector('[x-data]');
      if (appEl) {
        // @ts-ignore
        const alpine = appEl._x_dataStack?.[0];
        if (alpine) {
          alpine.previewUrl = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAA...';
          alpine.result = result;
          alpine.step = 3;
        }
      }
    }, mockResult);

    // Wait for results to render
    await page.waitForTimeout(500);

    // Check heading
    const heading = page.locator('h2:has-text("Your Transformation")');
    await expect(heading).toBeVisible();
  });

  test('should display shopping list items', async ({ page }) => {
    await page.goto('/');

    await page.evaluate((result) => {
      const appEl = document.querySelector('[x-data]');
      if (appEl) {
        // @ts-ignore
        const alpine = appEl._x_dataStack?.[0];
        if (alpine) {
          alpine.previewUrl = 'data:image/jpeg;base64,test';
          alpine.result = result;
          alpine.step = 3;
        }
      }
    }, mockResult);

    await page.waitForTimeout(500);

    // Check shopping list section
    const shoppingList = page.getByTestId('shopping-list');
    await expect(shoppingList).toBeVisible();

    // Check item names (use first() to avoid strict mode violation)
    await expect(page.locator('h4:has-text("Modern Floor Lamp")').first()).toBeVisible();
    await expect(page.locator('h4:has-text("Woven Area Rug")').first()).toBeVisible();
  });

  test('should show reset button', async ({ page }) => {
    await page.goto('/');

    await page.evaluate((result) => {
      const appEl = document.querySelector('[x-data]');
      if (appEl) {
        // @ts-ignore
        const alpine = appEl._x_dataStack?.[0];
        if (alpine) {
          alpine.previewUrl = 'data:image/jpeg;base64,test';
          alpine.result = result;
          alpine.step = 3;
        }
      }
    }, mockResult);

    await page.waitForTimeout(500);

    const resetButton = page.getByTestId('reset-button');
    await expect(resetButton).toBeVisible();
    await expect(resetButton).toContainText('New Design');
  });

  test('should reset to homepage when clicking new design', async ({ page }) => {
    await page.goto('/');

    await page.evaluate((result) => {
      const appEl = document.querySelector('[x-data]');
      if (appEl) {
        // @ts-ignore
        const alpine = appEl._x_dataStack?.[0];
        if (alpine) {
          alpine.previewUrl = 'data:image/jpeg;base64,test';
          alpine.result = result;
          alpine.step = 3;
        }
      }
    }, mockResult);

    await page.waitForTimeout(500);

    // Click reset
    const resetButton = page.getByTestId('reset-button');
    await resetButton.click();

    // Should return to step 1
    await expect(page.getByTestId('upload-area')).toBeVisible({ timeout: 3000 });
  });

});


/**
 * Before/After Slider Tests
 */
test.describe('Comparison Slider', () => {

  test('should have comparison slider on results page', async ({ page }) => {
    await page.goto('/');

    // Set up results state
    await page.evaluate(() => {
      const appEl = document.querySelector('[x-data]');
      if (appEl) {
        // @ts-ignore
        const alpine = appEl._x_dataStack?.[0];
        if (alpine) {
          alpine.previewUrl = 'data:image/jpeg;base64,test';
          alpine.result = {
            generated_image_url: '/uploads/test.jpg',
            shopping_list: [],
            total_estimated_price: 0
          };
          alpine.step = 3;
        }
      }
    });

    await page.waitForTimeout(500);

    const slider = page.getByTestId('comparison-slider');
    await expect(slider).toBeVisible();
  });

});
