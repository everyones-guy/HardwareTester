import { test, expect } from '@playwright/test';

test('local guided workflow launches the browser engine and retains its result', async ({
  page,
}) => {
  await page.goto('/tests');
  await page.getByRole('button', { name: 'Start guided setup', exact: true }).click();
  const guide = page.getByRole('region', { name: 'Guided test setup' });
  await guide.getByRole('button', { name: 'Connect guided input' }).click();
  await guide.getByRole('button', { name: 'Choose test', exact: true }).click();
  await guide.getByRole('button', { name: 'Review readiness' }).click();
  await expect(guide).toContainText('Local simulator');
  await guide.getByRole('button', { name: 'Start guided test', exact: true }).click();
  await expect(guide).toContainText('Your test passed', { timeout: 10000 });
  await guide.getByRole('button', { name: 'Open guided report' }).click();
  await expect(page.getByRole('region', { name: 'Run report' })).toContainText('passed');
});
