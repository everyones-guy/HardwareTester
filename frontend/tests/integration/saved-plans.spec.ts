import { test, expect } from '@playwright/test';

test('saved plan catalog filters, pages, expands, and reveals edited plans', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  const ids: string[] = [];
  for (let i = 1; i <= 7; i++) {
    const response = await request.post('/api/lab/test-plans', {
      data: {
        name: `Catalog check ${i}`,
        description: 'Saved library coverage',
        kind: i === 7 ? 'relay' : 'temperature',
        steps: [
          {
            name: 'Sample',
            action: i === 1 ? 'wait' : 'read',
            ...(i === 1 ? { seconds: 3 } : { timeout: 2 }),
          },
        ],
      },
    });
    expect(response.ok()).toBeTruthy();
    ids.push((await response.json()).planId);
  }
  try {
    await page.goto('/plans');
    const library = page.getByRole('region', { name: 'Saved test plan library' });
    await library.getByLabel('Search test plans').fill('Catalog check');
    await library.getByLabel('Visible test plan cards').selectOption('2');
    await expect(library.locator('.plan-catalog-card')).toHaveCount(2);
    const first = library.getByRole('button', { name: 'Test plan Catalog check 1', exact: true });
    await first.focus();
    await page.keyboard.press('Enter');
    await expect(first).toHaveAttribute('aria-expanded', 'true');
    await expect(library).toContainText('3s configured waits');
    await library.getByRole('button', { name: 'Test plan Catalog check 2', exact: true }).click();
    await expect(first).toHaveAttribute('aria-expanded', 'false');
    await library.getByRole('button', { name: 'Next test plan page' }).click();
    await expect(
      library.getByRole('button', { name: 'Test plan Catalog check 3', exact: true }),
    ).toBeVisible();
    await library.getByLabel('Filter plan action').selectOption('wait');
    await expect(library.locator('.plan-catalog-card')).toHaveCount(1);
    await library.getByRole('button', { name: /Relay/ }).click();
    await expect(library).toContainText('No test plans match');
    await library.getByRole('button', { name: 'Clear plan filters' }).click();
    await library.getByLabel('Search test plans').fill('Catalog check 7');
    await library.getByRole('button', { name: 'Test plan Catalog check 7', exact: true }).click();
    await library.getByRole('button', { name: 'Edit', exact: true }).click();
    await page.getByLabel('Plan name', { exact: true }).fill('Renamed catalog check');
    await page.getByRole('button', { name: 'Save changes', exact: true }).click();
    await expect(library.getByLabel('Search test plans')).toHaveValue('');
    await expect(
      library.getByRole('button', { name: 'Test plan Renamed catalog check', exact: true }),
    ).toHaveAttribute('aria-expanded', 'true');
    await expect(library).toContainText('version 2');
    if (process.env.LAB_SCREENSHOT_DIR) {
      await page.setViewportSize({ width: 1440, height: 1100 });
      await library.screenshot({
        path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-saved-plans.png`,
      });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
  } finally {
    for (const id of ids) {
      const response = await request.get(`/api/lab/test-plans/${id}`);
      const plan = (await response.json()).plan;
      await request.delete(`/api/lab/test-plans/${id}`, { data: { version: plan.version } });
    }
  }
});
