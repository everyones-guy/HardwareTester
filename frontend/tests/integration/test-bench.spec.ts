import { test, expect } from '@playwright/test';

test('instrument bench guides hookup, compatible plans, scenarios, and results', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  const response = await request.post('/api/lab/test-plans', {
    data: {
      name: 'Bench valve only',
      kind: 'valve',
      steps: [{ name: 'Valve reading', action: 'read', timeout: 2 }],
    },
  });
  const id = (await response.json()).planId;
  try {
    await page.goto('/tests');
    const bench = page.getByRole('region', { name: 'Test bench controls' });
    await expect(bench.getByRole('button', { name: 'Run test', exact: true })).toBeDisabled();
    await expect(bench).toContainText('SETUP REQUIRED');
    await expect(bench.getByLabel('Test plan')).not.toContainText('Bench valve only');
    await bench.getByLabel('Target device').selectOption({ label: 'Intake valve' });
    await expect(bench.getByLabel('Test plan')).toContainText('Bench valve only');
    await bench.getByLabel('Test plan').selectOption(id);
    await bench.getByText('Inspect selected sequence', { exact: true }).click();
    await expect(bench).toContainText('Valve reading');
    await bench.getByRole('button', { name: 'Connect input', exact: true }).click();
    await expect(bench).toContainText('READY TO TEST');
    expect(
      (await bench.getByRole('region', { name: 'Signal monitor' }).getByRole('img').boundingBox())!
        .width,
    ).toBeGreaterThan(200);
    await expect(bench.getByRole('region', { name: 'Signal monitor' })).toContainText(
      'SIMULATED INPUT',
    );
    await bench.getByRole('button', { name: 'Run test', exact: true }).click();
    await expect(bench.locator('.result-heading .status')).toHaveText('passed', { timeout: 15000 });
    await expect(bench.getByRole('progressbar')).toHaveAttribute('value', '2');
    await bench.getByText('Emulator setup · Normal device response', { exact: true }).click();
    const scenario = bench.getByRole('region', { name: 'Emulator scenario' });
    await scenario.getByLabel('Choose emulator scenario').selectOption('preset-recovery');
    await scenario.getByRole('button', { name: 'Apply scenario', exact: true }).click();
    await expect(bench).toContainText('Scenario starts at read 1');
    const before = (await (await request.get('/api/lab')).json()).state.devices.find(
      (d: { name: string }) => d.name === 'Intake valve',
    ).scenarioCursor;
    await page.waitForTimeout(1200);
    const after = (await (await request.get('/api/lab')).json()).state.devices.find(
      (d: { name: string }) => d.name === 'Intake valve',
    ).scenarioCursor;
    expect(after).toBe(before);
    await bench.getByRole('button', { name: 'Run test', exact: true }).click();
    await expect(bench.locator('.result-heading .status')).toHaveText('failed', { timeout: 15000 });
    await scenario.getByRole('button', { name: 'Clear scenario', exact: true }).click();
    await bench.getByRole('button', { name: 'Run selected setup again' }).click();
    await expect(bench.locator('.result-heading .status')).toHaveText('passed', { timeout: 15000 });
    const download = page.waitForEvent('download');
    await bench.getByRole('button', { name: 'Export run', exact: true }).click();
    expect((await download).suggestedFilename()).toBe('hardware-tester-run.json');
    if (process.env.LAB_SCREENSHOT_DIR) {
      await page.setViewportSize({ width: 1800, height: 1250 });
      await bench.screenshot({
        path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-instrument-bench.png`,
      });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
    await bench.getByRole('button', { name: 'Inspect report' }).click();
    await expect(page.getByRole('region', { name: 'Run report' })).toBeVisible();
  } finally {
    await request.delete(`/api/lab/test-plans/${id}`, { data: { version: 1 } });
  }
});
