import { test, expect } from '@playwright/test';
test('connection checks report faults and recovery without starting a run', async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem('hardware-tester.engine', 'browser'));
  await page.goto('/overview');
  const diagnostic = page.getByRole('region', { name: 'Connection diagnostics' });
  const check = page.getByRole('button', { name: 'Test connection', exact: true });
  await check.click();
  await expect(diagnostic.locator('.connection-check').first()).toContainText(
    'Device disconnected',
  );
  await page.getByRole('button', { name: 'Connect bench', exact: true }).click();
  await check.click();
  await expect(diagnostic.locator('.connection-check').first()).toContainText('Responding');
  await page.getByLabel('Fault injection').selectOption('timeout');
  await check.click();
  await expect(diagnostic.locator('.connection-check').first()).toContainText('transport timeout');
  await page.getByLabel('Fault injection').selectOption('out-of-range');
  await check.click();
  await expect(diagnostic.locator('.connection-check').first()).toContainText(
    'Reading out of range',
  );
  await page.getByLabel('Fault injection').selectOption('none');
  await check.click();
  await expect(diagnostic.locator('.connection-check').first()).toContainText('Responding');
  await expect(diagnostic.locator('.connection-check')).toHaveCount(5);
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(check).toBeDisabled();
  await expect(page.locator('.result-heading .status')).toHaveText('passed');
  await expect(check).toBeEnabled();
});
