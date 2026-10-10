import { test, expect } from '@playwright/test';

test('saved suite runs expected failures and recovery, exports snapshots, and cancels', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  await request.post('/api/lab/connect-bench', { data: {} });
  await page.goto('/suites');
  await page.getByLabel('Suite name', { exact: true }).fill('Browser regression suite');
  await page.getByRole('button', { name: 'Save validation suite', exact: true }).click();
  await expect(page.getByLabel('Validation suite', { exact: true })).toContainText(
    'Browser regression suite',
  );
  const suiteId = await page.getByLabel('Validation suite', { exact: true }).inputValue();
  try {
    await page.getByLabel('Suite target device').selectOption({ label: 'Ambient temperature' });
    await page.getByRole('button', { name: 'Run suite', exact: true }).click();
    const report = page.getByRole('region', { name: 'Validation suite report' });
    await expect(report).toContainText('Every test outcome matched its expectation.', {
      timeout: 30000,
    });
    await expect(report.getByText('Expected failure detected', { exact: true })).toHaveCount(2);
    await expect(report.getByText('Expected pass confirmed', { exact: true })).toHaveCount(2);
    const download = page.waitForEvent('download');
    await report.getByRole('button', { name: 'Export suite report' }).click();
    const stream = await (await download).createReadStream();
    const chunks: Buffer[] = [];
    for await (const c of stream!) chunks.push(c);
    const exported = JSON.parse(Buffer.concat(chunks).toString());
    expect(exported.report.status).toBe('passed');
    expect(
      exported.report.cases[2].attempts.map((a: { run: { status: string } }) => a.run.status),
    ).toEqual(['failed', 'passed']);
    if (process.env.LAB_SCREENSHOT_DIR) {
      await page.setViewportSize({ width: 1440, height: 1100 });
      await report.screenshot({
        path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-validation-suite.png`,
      });
    }
    await report.getByRole('button', { name: 'Inspect test report' }).nth(1).click();
    await expect(page.getByRole('region', { name: 'Run report' })).toContainText('failed');
    await page.goto('/suites');
    await page.getByLabel('Validation suite', { exact: true }).selectOption(suiteId);
    await page.getByLabel('Suite target device').selectOption({ label: 'Ambient temperature' });
    await page.getByRole('button', { name: 'Run suite', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Stop suite', exact: true })).toBeEnabled();
    await page.reload();
    await expect(page.getByRole('button', { name: 'Stop suite', exact: true })).toBeEnabled();
    await page.getByRole('button', { name: 'Stop suite', exact: true }).click();
    await expect(report).toContainText('cancelled');
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
    const state = (await (await request.get('/api/lab')).json()).state;
    expect(
      state.devices.find((d: { name: string }) => d.name === 'Ambient temperature').scenario,
    ).toBeUndefined();
  } finally {
    await request.delete(`/api/lab/validation-suites/${suiteId}`, { data: { version: 1 } });
  }
});
