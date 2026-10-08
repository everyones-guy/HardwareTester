import { test, expect } from '@playwright/test';

test('scenario catalog filters and pages cards while long stage edits remain intact', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  const existing = (await (await request.get('/api/lab')).json()).state;
  for (const s of existing.scenarios.filter((s: { name: string }) =>
    s.name.startsWith('Index pattern '),
  ))
    await request.delete(`/api/lab/scenarios/${s.id}`, { data: { version: s.version } });
  const ids: string[] = [];
  for (let n = 1; n <= 8; n++) {
    const frames =
      n === 1
        ? Array.from({ length: 20 }, (_, i) =>
            i === 0
              ? { behavior: 'delay', count: 1, delayMs: 250 }
              : i === 1
                ? { behavior: 'timeout', count: 1 }
                : { behavior: 'healthy', count: 1 },
          )
        : [{ behavior: 'healthy', count: 1 }];
    const result = await request.post('/api/lab/scenarios', {
      data: { name: `Index pattern ${n}`, description: 'Catalog test sequence', frames },
    });
    expect(result.ok()).toBeTruthy();
    ids.push((await result.json()).scenarioId);
  }
  const device = (await (await request.get('/api/lab')).json()).state.devices[0];
  await request.post(`/api/lab/devices/${device.id}/scenario`, { data: { scenarioId: ids[0] } });
  await page.goto('/scenarios');
  const library = page.getByRole('region', { name: 'Saved scenario library' });
  await page.getByLabel('Search scenarios').fill('Index pattern');
  await page.getByLabel('Visible scenario cards').selectOption('2');
  await page.getByLabel('Sort scenarios').selectOption('name');
  await expect(library.locator('.scenario-card')).toHaveCount(2);
  const first = library.getByRole('button', { name: 'Scenario Index pattern 1', exact: true });
  await expect(first).toContainText('1 in use');
  await first.focus();
  await page.keyboard.press('Enter');
  await expect(first).toHaveAttribute('aria-expanded', 'true');
  await expect(library).toContainText('Final behavior repeats: Healthy response');
  await library.getByRole('button', { name: 'Scenario Index pattern 2', exact: true }).click();
  await expect(first).toHaveAttribute('aria-expanded', 'false');
  await library.getByRole('button', { name: 'Next scenario page' }).click();
  await expect(
    library.getByRole('button', { name: 'Scenario Index pattern 3', exact: true }),
  ).toBeVisible();
  await expect(library.locator('.scenario-card-details')).toHaveCount(0);
  await page.getByLabel('Filter scenario behavior').selectOption('delay');
  await expect(library.locator('.scenario-card')).toHaveCount(1);
  await page.getByLabel('Search scenarios').fill('no matching sequence');
  await expect(library.getByRole('heading', { name: 'No scenarios match' })).toBeVisible();
  await library.getByRole('button', { name: 'Clear scenario filters' }).click();
  await library
    .getByRole('group', { name: 'Filter scenario type' })
    .getByRole('button', { name: /Presets/ })
    .click();
  await expect(library.locator('.scenario-card-name small')).toHaveText([/Preset/, /Preset/]);
  await library
    .getByRole('group', { name: 'Filter scenario type' })
    .getByRole('button', { name: /Custom/ })
    .click();
  await page.getByLabel('Search scenarios').fill('Index pattern 1');
  await first.click();
  await library.getByRole('button', { name: 'Edit', exact: true }).click();
  const editor = page.getByRole('region', { name: 'Scenario editor' });
  await expect(editor.locator('.scenario-stage')).toHaveCount(20);
  await expect(editor.locator('.scenario-frame')).toHaveCount(0);
  await editor.getByRole('button', { name: 'Edit stage 1', exact: true }).click();
  await page.getByLabel('Stage 1 delay').fill('2001');
  await editor.getByRole('button', { name: 'Collapse all stages' }).click();
  await expect(editor.locator('.scenario-stage-error')).toContainText(
    'Delay must be 0–2000 milliseconds.',
  );
  await expect(editor.getByRole('button', { name: 'Save scenario changes' })).toBeDisabled();
  await editor.getByRole('button', { name: 'Edit stage 1', exact: true }).click();
  await page.getByLabel('Stage 1 delay').fill('400');
  await editor.getByRole('button', { name: 'Edit stage 2', exact: true }).click();
  await editor.getByRole('button', { name: 'Move stage 2 up', exact: true }).click();
  await expect(page.getByLabel('Stage 2 delay')).toHaveValue('400');
  await editor.getByRole('button', { name: 'Remove stage 1', exact: true }).click();
  await editor.getByRole('button', { name: 'Add stage', exact: true }).click();
  await expect(page.getByLabel('Stage 20 reads')).toBeVisible();
  await editor.getByRole('button', { name: 'Save scenario changes' }).click();
  await expect(
    library.getByRole('heading', { name: 'Index pattern 1', exact: true }),
  ).toBeVisible();
  await expect(library).toContainText('CUSTOM · v2');
  await expect(library).toContainText('snapshot v1');
  const updated = (await (await request.get('/api/lab')).json()).state.scenarios.find(
    (s: { id: string }) => s.id === ids[0],
  );
  expect(updated.frames).toHaveLength(20);
  expect(updated.frames[0].delayMs).toBe(400);
  await page.getByLabel('Search scenarios').fill('');
  await page.getByLabel('Visible scenario cards').selectOption('5');
  await page.getByLabel('Sort scenarios').selectOption('presets');
  await library
    .getByRole('group', { name: 'Filter scenario type' })
    .getByRole('button', { name: /All patterns/ })
    .click();
  await library.getByRole('button', { name: 'Scenario Intermittent timeout', exact: true }).click();
  if (process.env.LAB_SCREENSHOT_DIR) {
    await page.setViewportSize({ width: 1440, height: 1100 });
    await library.screenshot({
      path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-scenario-catalog.png`,
    });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  for (let i = 0; i < ids.length; i++)
    await request.delete(`/api/lab/scenarios/${ids[i]}`, { data: { version: i === 0 ? 2 : 1 } });
});
