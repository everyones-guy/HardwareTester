import { test, expect } from '@playwright/test';

test('blueprint cards filter, page, preview devices, export, apply, and delete', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  const ids: string[] = [];
  for (let i = 1; i <= 7; i++) {
    const response = await request.post('/api/lab/blueprints', {
      data: {
        configuration: {
          name: `Catalog blueprint ${i}`,
          description: 'Reusable controller configuration',
          peripherals: [
            { name: `Probe ${i}`, type: i === 7 ? 'relay' : 'temperature_sensor' },
            ...(i === 1 ? [{ name: 'Unsupported probe', type: 'ph_sensor' }] : []),
          ],
        },
      },
    });
    expect(response.ok()).toBeTruthy();
    ids.push((await response.json()).blueprintId);
  }
  try {
    await page.goto('/blueprints');
    const library = page.getByRole('region', { name: 'Saved blueprint library' });
    await library.getByLabel('Search blueprints').fill('Catalog blueprint');
    await library.getByLabel('Visible blueprint cards').selectOption('2');
    await expect(library.locator('.blueprint-catalog-card')).toHaveCount(2);
    const first = library.getByRole('button', {
      name: 'Blueprint Catalog blueprint 1',
      exact: true,
    });
    await first.focus();
    await page.keyboard.press('Enter');
    await expect(first).toHaveAttribute('aria-expanded', 'true');
    await expect(library.getByLabel('Blueprint devices')).toContainText('Probe 1');
    await library.getByText('Import notes · 2', { exact: true }).click();
    await expect(library).toContainText('Unsupported probe: unsupported type');
    const downloaded = page.waitForEvent('download');
    await library.getByRole('button', { name: 'Export JSON' }).click();
    expect((await downloaded).suggestedFilename()).toBe('blueprint.json');
    await library
      .getByRole('button', { name: 'Blueprint Catalog blueprint 2', exact: true })
      .click();
    await expect(first).toHaveAttribute('aria-expanded', 'false');
    await library.getByRole('button', { name: 'Next blueprint page' }).click();
    await expect(
      library.getByRole('button', { name: 'Blueprint Catalog blueprint 3', exact: true }),
    ).toBeVisible();
    await library.getByRole('button', { name: /Relay/ }).click();
    await expect(library.locator('.blueprint-catalog-card')).toHaveCount(1);
    await library.getByLabel('Search blueprints').fill('no such blueprint');
    await expect(library).toContainText('No blueprints match');
    await library.getByRole('button', { name: 'Clear blueprint filters' }).click();
    await library.getByLabel('Search blueprints').fill('Probe 7');
    await library
      .getByRole('button', { name: 'Blueprint Catalog blueprint 7', exact: true })
      .click();
    const before = (await (await request.get('/api/lab')).json()).state.devices.length;
    await library.getByRole('button', { name: 'Add to bench', exact: true }).click();
    await expect(page.getByLabel('Peripheral device')).toContainText('Probe 7');
    const after = (await (await request.get('/api/lab')).json()).state;
    expect(after.devices).toHaveLength(before + 1);
    expect(after.devices.find((d: { name: string }) => d.name === 'Probe 7').connected).toBe(false);
    await library.getByLabel('Search blueprints').fill('Catalog blueprint');
    await library.getByLabel('Sort blueprints').selectOption('devices');
    await library.getByLabel('Visible blueprint cards').selectOption('5');
    await library
      .getByRole('button', { name: 'Blueprint Catalog blueprint 1', exact: true })
      .click();
    if (process.env.LAB_SCREENSHOT_DIR)
      await library.screenshot({
        path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-blueprint-catalog.png`,
      });
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
    page.once('dialog', (dialog) => dialog.accept());
    await library.getByRole('button', { name: 'Delete', exact: true }).click();
    await expect(
      library.getByRole('button', { name: 'Blueprint Catalog blueprint 1', exact: true }),
    ).toHaveCount(0);
  } finally {
    for (const id of ids) await request.delete(`/api/lab/blueprints/${id}`);
  }
});
