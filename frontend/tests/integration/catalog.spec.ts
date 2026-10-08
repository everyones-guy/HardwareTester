import { test, expect } from '@playwright/test';

test('blueprint import, apply, and peripheral editing work through Flask', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  const state = (await (await request.get('/api/lab')).json()).state;
  for (const b of state.blueprints)
    await request.delete(`/api/lab/blueprints/${b.id}`, { data: {} });
  await page.goto('/blueprints');
  await expect(page.getByText('Flask engine connected')).toBeVisible();
  await page.getByLabel('Blueprint JSON', { exact: true }).fill(
    JSON.stringify({
      name: 'Controller demo',
      peripherals: [
        { name: 'Imported temperature', type: 'temperature_sensor', threshold: 50 },
        { name: 'Legacy pH', type: 'ph_sensor' },
      ],
    }),
  );
  await page.getByRole('button', { name: 'Preview import', exact: true }).click();
  await expect(page.getByText('Controller demo · 1 devices')).toBeVisible();
  await expect(page.getByText(/Legacy pH: unsupported type/)).toBeVisible();
  await page.getByRole('button', { name: 'Save blueprint', exact: true }).click();
  await page.getByRole('button', { name: 'Add to bench', exact: true }).click();
  await expect(page.getByLabel('Peripheral device')).toContainText('Imported temperature');
  const peripheral = page
    .locator('.catalog-item')
    .filter({ has: page.getByRole('heading', { name: 'Imported temperature', exact: true }) });
  await peripheral.getByRole('button', { name: 'Edit properties', exact: true }).click();
  await page.getByLabel('Peripheral properties').fill('{"threshold":{"min":0,"max":10}}');
  await page.getByRole('button', { name: 'Save properties', exact: true }).click();
  await expect(peripheral.locator('pre')).toContainText('10');
  await page.getByLabel('Capture blueprint name').fill('Captured bench');
  await page.getByRole('button', { name: 'Save current bench', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Captured bench', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Controller demo', exact: true })).toBeVisible();
  const final = (await (await request.get('/api/lab')).json()).state;
  expect(final.devices).toHaveLength(4);
  expect(final.peripherals[0].properties.threshold.max).toBe(10);
  await page.screenshot({
    path: 'C:/Users/Gary/Documents/Codex/2026-10-05/i-v/outputs/hardware-tester-blueprints.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBeTruthy();
});
