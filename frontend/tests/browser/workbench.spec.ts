import { test, expect, Page } from '@playwright/test';
async function connectBench(page: Page) {
  await page.goto('/overview');
  await page.getByRole('button', { name: 'Connect bench', exact: true }).click();
}
async function runAndWait(page: Page, result: string) {
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText(result);
}
test('healthy devices pass checks; faults fail; export contains the results', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await connectBench(page);
  for (const name of ['Ambient temperature', 'Intake valve', 'Pump relay']) {
    await page.getByLabel('Target device').selectOption({ label: name });
    await runAndWait(page, 'passed');
  }
  await page.getByLabel('Fault injection').selectOption('out-of-range');
  await runAndWait(page, 'failed');
  await expect(page.locator('.step-failed')).toContainText('outside expected range');
  await page.getByLabel('Fault injection').selectOption('timeout');
  await runAndWait(page, 'failed');
  await expect(page.locator('.step-failed').first()).toContainText('transport timeout');
  await page.getByLabel('Fault injection').selectOption('none');
  await page.getByRole('link', { name: 'Results', exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(5);
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export results', exact: true }).click();
  const file = await download;
  const stream = await file.createReadStream();
  const chunks: Buffer[] = []; for await (const c of stream!) chunks.push(c);
  const report = JSON.parse(Buffer.concat(chunks).toString());
  expect(report.mode).toBe('simulation'); expect(report.runs).toHaveLength(5);
  expect(errors).toEqual([]);
});
test('control responses execute and restore valve and relay states', async ({ page }) => {
  await connectBench(page);
  await page.getByLabel('Test plan').selectOption('control');
  await page.getByLabel('Target device').selectOption({ label: 'Intake valve' });
  await runAndWait(page, 'passed');
  await expect(page.locator('.inspect-reading')).toContainText('0%');
  await expect(page.locator('.steps')).toContainText('Observed expected response: 75%');
  await page.getByLabel('Target device').selectOption({ label: 'Pump relay' });
  await runAndWait(page, 'passed');
  await expect(page.locator('.inspect-reading')).toContainText('OFF');
  await page.getByLabel('Target device').selectOption({ label: 'Ambient temperature' });
  await runAndWait(page, 'passed');
  await expect(page.locator('.steps')).toContainText('Observed expected response: 30°C');
});
test('cancel restores original controls and a disconnect is caught during execution', async ({ page }) => {
  await connectBench(page);
  await page.getByLabel('Target device').selectOption({ label: 'Intake valve' });
  await page.getByLabel('Test plan').selectOption('control');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.inspect-reading')).toContainText('75%');
  await page.getByRole('button', { name: 'Stop test', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText('cancelled');
  await expect(page.locator('.inspect-reading')).toContainText('0%');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await page.getByRole('button', { name: 'Disconnect device', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText('failed');
  await expect(page.locator('.step-failed').first()).toContainText('Device disconnected');
});
test('reload preserves history and cancels interrupted tests', async ({ page }) => {
  await connectBench(page);
  await page.getByLabel('Target device').selectOption({ label: 'Intake valve' });
  await page.getByLabel('Test plan').selectOption('control');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.inspect-reading')).toContainText('75%');
  await page.reload();
  await expect(page.locator('.result-heading .status')).toHaveText('cancelled');
  await page.getByLabel('Target device').selectOption({ label: 'Intake valve' });
  await expect(page.locator('.inspector .status')).toHaveText('offline');
  await page.getByRole('button', { name: 'Connect device', exact: true }).click();
  await expect(page.locator('.inspect-reading')).toContainText('0%');
});
test('add, search, control, and remove a virtual relay', async ({ page }) => {
  await page.goto('/devices');
  await page.getByRole('button', { name: 'Add device', exact: true }).click();
  await page.getByLabel('Device name').fill('Outlet relay');
  await page.getByLabel('Hardware profile').selectOption('relay');
  await page.getByRole('button', { name: 'Add to bench' }).click();
  await expect(page.locator('.inspector h2')).toHaveText('Outlet relay');
  await page.getByLabel('Search devices').fill('Outlet');
  await expect(page.locator('.device-card')).toHaveCount(1);
  await page.getByRole('button', { name: 'Connect device', exact: true }).click();
  await page.getByRole('button', { name: 'Switch ON', exact: true }).click();
  await expect(page.locator('.inspect-reading')).toContainText('ON');
  await page.getByRole('button', { name: 'Remove device' }).click();
  await expect(page.locator('.device-card')).toHaveCount(0);
  await expect(page.getByText('No devices match your search.')).toBeVisible();
});
test('mobile layout and direct route reloads work without horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await connectBench(page);
  await runAndWait(page, 'passed');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.goto('/results');
  await expect(page.getByRole('heading', { name: 'Test results', exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator('tbody tr')).toHaveCount(1);
});
