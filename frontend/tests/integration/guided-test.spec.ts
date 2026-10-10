import { test, expect } from '@playwright/test';

test('guided test connects, runs, preserves progress, reruns a fault, and opens its report', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  await page.goto('/tests');
  const bench = page.getByRole('region', { name: 'Test bench controls' });
  await bench.getByRole('button', { name: 'Start guided setup', exact: true }).click();
  const guide = page.getByRole('region', { name: 'Guided test setup' });
  await expect(guide.getByRole('button', { name: 'Choose test', exact: true })).toBeDisabled();
  await guide
    .getByLabel('Guided input')
    .selectOption({ label: 'Ambient temperature · simulation' });
  await guide.getByRole('button', { name: 'Connect guided input', exact: true }).click();
  await guide.getByRole('button', { name: 'Choose test', exact: true }).click();
  await guide.getByLabel('Guided sequence').selectOption('control');
  await expect(guide).toContainText('Commands output:');
  await guide.getByLabel('Guided sequence').selectOption('smoke');
  await expect(guide).toContainText('Read-only test:');
  await guide.getByRole('button', { name: 'Review readiness' }).click();
  await expect(guide).toContainText('Ready for the first reading');
  await guide.getByRole('button', { name: 'Start guided test', exact: true }).click();
  await expect(guide).toContainText('Your test passed', { timeout: 15000 });
  await expect(guide.locator('.guided-measurement.passed')).toHaveCount(3);
  await expect(guide).toContainText('Expected:');
  await bench.getByRole('button', { name: 'Close guided setup' }).click();
  await expect(guide).toBeHidden();
  await bench.getByRole('button', { name: 'Start guided setup' }).click();
  await expect(guide).toContainText('Your test passed');
  await guide.getByRole('button', { name: 'Review & rerun' }).click();
  await guide.getByRole('button', { name: 'Back to test' }).click();
  await guide.getByText('Optional simulation scenario', { exact: true }).click();
  await guide.getByLabel('Choose emulator scenario').selectOption('preset-sustained-bad-reading');
  await guide.getByRole('button', { name: 'Apply scenario', exact: true }).click();
  await expect(guide).toContainText('Applied scenario: Sustained bad telemetry');
  await guide.getByRole('button', { name: 'Review readiness' }).click();
  await guide.getByRole('button', { name: 'Start guided test', exact: true }).click();
  await expect(guide).toContainText('Your test found a problem', { timeout: 15000 });
  await expect(guide.locator('.guided-measurement.failed')).toHaveCount(1);
  if (process.env.LAB_SCREENSHOT_DIR) {
    await page.setViewportSize({ width: 1500, height: 1100 });
    await guide.screenshot({
      path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-guided-result.png`,
    });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
  await guide.getByRole('button', { name: 'Open guided report' }).click();
  await expect(page.getByRole('region', { name: 'Run report' })).toContainText('failed');
});

test('guided setup explains disabled hardware and never opens a transport', async ({ page }) => {
  let mutations = 0;
  await page.route('**/api/lab', async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.capabilities = { hardware: false };
    data.state.devices = [
      {
        ...data.state.devices[0],
        id: 'disabled-serial',
        name: 'Pi serial responder',
        adapter: 'serial',
        endpoint: 'COM-PI',
        connected: false,
      },
    ];
    data.state.runs = [];
    data.state.suiteRuns = [];
    await route.fulfill({ response, json: data });
  });
  await page.route('**/api/lab/devices/**', async (route) => {
    mutations++;
    await route.abort();
  });
  await page.goto('/tests');
  await page.getByRole('button', { name: 'Start guided setup', exact: true }).click();
  const guide = page.getByRole('region', { name: 'Guided test setup' });
  await expect(guide).toContainText('matching request ID');
  await expect(guide.getByRole('button', { name: 'Connect guided input' })).toBeDisabled();
  await guide.getByRole('button', { name: '3 Check & run' }).click();
  await expect(guide).toContainText('Hardware disabled on the server');
  await expect(
    guide.getByRole('button', { name: 'Start guided test', exact: true }),
  ).toBeDisabled();
  expect(mutations).toBe(0);
});

test('guided test can be stopped and reports cancellation', async ({ page, request }) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  await request.post('/api/lab/connect-bench', { data: {} });
  const created = await request.post('/api/lab/test-plans', {
    data: {
      name: 'Guided cancellation',
      kind: 'temperature',
      steps: [{ name: 'Wait for operator', action: 'wait', seconds: 10 }],
    },
  });
  const id = (await created.json()).planId;
  try {
    await page.goto('/tests');
    await page.getByRole('button', { name: 'Start guided setup', exact: true }).click();
    const guide = page.getByRole('region', { name: 'Guided test setup' });
    await guide.getByRole('button', { name: 'Choose test', exact: true }).click();
    await guide.getByLabel('Guided sequence').selectOption(id);
    await guide.getByRole('button', { name: 'Review readiness' }).click();
    await guide.getByRole('button', { name: 'Start guided test', exact: true }).click();
    await guide.getByRole('button', { name: 'Stop guided test', exact: true }).click();
    await expect(guide).toContainText('Your test was stopped');
  } finally {
    await request.post('/api/lab/runs/cancel', { data: {} });
    await request.delete(`/api/lab/test-plans/${id}`, { data: { version: 1 } });
  }
});

test('guided launch rejection stays on readiness and never shows an older verdict', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  await request.post('/api/lab/connect-bench', { data: {} });
  await page.route('**/api/lab/runs', async (route) => {
    await route.fulfill({ status: 409, json: { error: 'The bench changed. Refresh and retry.' } });
  });
  await page.goto('/tests');
  await page.getByRole('button', { name: 'Start guided setup', exact: true }).click();
  const guide = page.getByRole('region', { name: 'Guided test setup' });
  await guide.getByRole('button', { name: '3 Check & run' }).click();
  await guide.getByRole('button', { name: 'Start guided test', exact: true }).click();
  await expect(guide.getByRole('alert')).toContainText('The test did not start');
  await expect(guide.getByRole('button', { name: 'Start guided test', exact: true })).toBeEnabled();
  await expect(guide.getByRole('button', { name: '4 Read result' })).toBeDisabled();
});

test('suite ownership blocks guided launch between test attempts', async ({ page }) => {
  await page.route('**/api/lab', async (route) => {
    const response = await route.fetch();
    const data = await response.json();
    data.state.runs = [];
    data.state.suiteRuns = [{ id: 'ownership-check', status: 'running', cases: [] }];
    await route.fulfill({ response, json: data });
  });
  await page.goto('/tests');
  await page.getByRole('button', { name: 'Start guided setup', exact: true }).click();
  const guide = page.getByRole('region', { name: 'Guided test setup' });
  await guide.getByRole('button', { name: '3 Check & run' }).click();
  await expect(guide).toContainText('A validation suite owns the bench');
  await expect(
    guide.getByRole('button', { name: 'Start guided test', exact: true }),
  ).toBeDisabled();
});
