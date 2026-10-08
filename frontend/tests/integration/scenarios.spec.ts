import { test, expect } from '@playwright/test';
test('saved emulator sequences exercise diagnostics, restart, and timed test failures', async ({
  page,
  request,
}) => {
  test.setTimeout(60000);
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  const state = (await (await request.get('/api/lab')).json()).state;
  for (const s of state.scenarios.filter((s: { name: string }) => s.name === 'Browser recovery'))
    await request.delete(`/api/lab/scenarios/${s.id}`, { data: { version: s.version } });
  await page.goto('/scenarios');
  await expect(page.getByRole('heading', { name: 'Healthy device', exact: true })).toBeVisible();
  await page.getByLabel('Scenario name', { exact: true }).fill('Browser recovery');
  await page.getByLabel('Stage 1 reads').fill('1');
  await page.getByRole('button', { name: 'Save scenario', exact: true }).click();
  const saved = page
    .locator('.scenario-card')
    .filter({ has: page.getByRole('heading', { name: 'Browser recovery', exact: true }) });
  await expect(saved).toContainText('CUSTOM · v1');
  if (process.env.LAB_SCREENSHOT_DIR) {
    await page.setViewportSize({ width: 1440, height: 1100 });
    await page.evaluate(() => scrollTo(0, 0));
    await page.screenshot({
      path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-emulator-scenarios.png`,
    });
  }
  const created = (await (await request.get('/api/lab')).json()).state.scenarios.find(
    (s: { name: string }) => s.name === 'Browser recovery',
  );
  const downloadPromise = page.waitForEvent('download');
  await saved.getByRole('button', { name: 'Export', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('emulator-scenario.json');
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(chunk);
  const exported = JSON.parse(Buffer.concat(chunks).toString());
  expect(exported.frames).toEqual(created.frames);
  await page.getByLabel('Import scenario JSON').setInputFiles({
    name: 'scenario.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify({ ...exported, name: 'Imported recovery' })),
  });
  await expect(page.getByRole('heading', { name: 'Imported recovery', exact: true })).toBeVisible();
  const imported = (await (await request.get('/api/lab')).json()).state.scenarios.find(
    (s: { name: string }) => s.name === 'Imported recovery',
  );
  expect(imported.builtin).toBe(false);
  await request.delete(`/api/lab/scenarios/${imported.id}`, {
    data: { version: imported.version },
  });
  await page.getByRole('link', { name: 'Devices', exact: true }).click();
  await page.getByLabel('Choose emulator scenario').selectOption(created.id);
  await page.getByRole('button', { name: 'Apply scenario', exact: true }).click();
  const controls = page.getByRole('region', { name: 'Emulator scenario' });
  await expect(controls).toContainText('Browser recovery · v1');
  await expect(page.getByLabel('Fault injection')).toBeDisabled();
  await page.getByRole('button', { name: 'Connect device', exact: true }).click();
  const checks = page.locator('.connection-check');
  await page.getByRole('button', { name: 'Test connection', exact: true }).click();
  await expect(checks.first()).toContainText('Scenario timeout');
  await page.getByRole('button', { name: 'Test connection', exact: true }).click();
  await expect(checks.first()).toContainText('Responding');
  await expect(controls).toContainText('2 / 2 staged reads consumed');
  await page.getByRole('button', { name: 'Restart sequence', exact: true }).click();
  await page.getByRole('button', { name: 'Test connection', exact: true }).click();
  await expect(checks.first()).toContainText('Scenario timeout');
  await page.getByRole('button', { name: 'Clear scenario', exact: true }).click();
  await expect(page.getByLabel('Fault injection')).toBeEnabled();
  await page.getByRole('button', { name: 'Test connection', exact: true }).click();
  await expect(checks.first()).toContainText('Responding');
  await page.getByLabel('Choose emulator scenario').selectOption('preset-delayed');
  await page.getByRole('button', { name: 'Apply scenario', exact: true }).click();
  const plan = await request.post('/api/lab/test-plans', {
    data: {
      name: 'Scenario short timeout',
      kind: 'temperature',
      steps: [{ name: 'Fast read', action: 'read', timeout: 0.1 }],
    },
  });
  await page.getByRole('link', { name: 'Test bench', exact: true }).click();
  await page.getByLabel('Test plan', { exact: true }).selectOption((await plan.json()).planId);
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText('failed');
  await expect(page.locator('.step-failed')).toContainText(
    'Scenario response exceeded its timeout',
  );
  await page.getByRole('link', { name: 'Results', exact: true }).click();
  const report = page.getByRole('region', { name: 'Run report' });
  await expect(report).toContainText('Fast read');
  await report.getByText(/Configuration captured for this run/).click();
  await expect(page.locator('.run-configuration')).toContainText('Delayed responses');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('link', { name: 'Emulator scenarios', exact: true }).click();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
});
