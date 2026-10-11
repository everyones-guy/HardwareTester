import { test, expect } from '@playwright/test';

test('compares recorded values, filters changed setups, and persists a replacement baseline', async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem('hardware-tester.engine', 'browser');
    if (localStorage.getItem('hardware-tester.lab.v1')) return;
    const device = {
      id: 'result-device',
      name: 'Bench temperature',
      kind: 'temperature',
      protocol: 'MQTT',
      endpoint: 'sim://mqtt/lab/temperature',
      connected: false,
      fault: 'none',
      value: 24,
      enabled: false,
    };
    const names = ['Connection handshake', 'Read telemetry', 'Validate operating range'];
    const runs = [95, 25, 24].map((value, index) => ({
      id: `result-${index}`,
      deviceId: device.id,
      deviceName: device.name,
      plan: 'Connection & health',
      planId: 'smoke',
      startedAt: `2026-10-10T12:0${3 - index}:00Z`,
      finishedAt: `2026-10-10T12:0${3 - index}:02Z`,
      status: index === 0 ? 'failed' : 'passed',
      baseline: index === 2,
      restoration: 'not-needed',
      configuration: {
        device: { ...device, fault: index === 0 ? 'out-of-range' : 'none' },
        plan: { id: 'smoke', name: 'Connection & health', version: 1, steps: names },
        peripherals: [],
        workspaceRevision: index,
      },
      steps: names.map((name, i) => ({
        name,
        status: index === 0 && i === 2 ? 'failed' : 'passed',
        observed: i > 0 ? value : undefined,
        expected: i === 2 ? { min: 0, max: 50 } : undefined,
        durationMs: 10,
        detail: 'Recorded check',
      })),
    }));
    localStorage.setItem(
      'hardware-tester.lab.v1',
      JSON.stringify({ version: 1, devices: [device], runs, logs: [] }),
    );
  });
  await page.goto('/results');
  const analysis = page.getByRole('region', { name: 'Result comparison and trends' });
  await expect(analysis).toContainText('1 checks regressed');
  await expect(analysis).toContainText('Injected fault');
  await expect(analysis).toContainText('+71°C');
  await expect(analysis.getByRole('button', { name: 'Use this run as baseline' })).toBeDisabled();
  await expect(analysis).toContainText('2 runs with changed or missing configuration excluded');
  await analysis.getByLabel('Trend metric').selectOption('2');
  await expect(analysis).toContainText('Shaded expected range: 0°C to 50°C');
  await analysis.getByLabel('Include changed configurations').check();
  await expect(analysis.getByRole('img', { name: /History trend: 3 readings/ })).toBeVisible();
  expect((await analysis.locator('.trend-chart').boundingBox())!.width).toBeGreaterThan(300);
  await analysis.getByText('View plotted runs and exact values (3)').click();
  await expect(analysis.locator('.trend-record')).toHaveCount(3);
  if (process.env.LAB_SCREENSHOT_DIR)
    await analysis.screenshot({
      path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-result-comparison.png`,
    });
  await page.locator('tbody tr').nth(1).getByRole('button', { name: 'Inspect' }).click();
  await analysis.getByRole('button', { name: 'Use this run as baseline' }).click();
  await expect(analysis.getByRole('button', { name: 'Clear baseline' })).toBeEnabled();
  await page.reload();
  await expect(analysis.getByLabel('Reference run')).toHaveValue('result-1');
  expect(
    await page.evaluate(() =>
      JSON.parse(localStorage.getItem('hardware-tester.lab.v1')!)
        .runs.filter((r: { baseline?: boolean }) => r.baseline)
        .map((r: { id: string }) => r.id),
    ),
  ).toEqual(['result-1']);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  ).toBeTruthy();
});
