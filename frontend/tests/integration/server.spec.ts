import { test, expect } from '@playwright/test';
test.beforeEach(async ({ request }) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  const response = await request.post('/api/lab/reset', { data: {} });
  expect(response.ok()).toBeTruthy();
});
test('React uses Flask for connections, tests, faults, and shared run persistence', async ({ page }) => {
  await page.goto('/overview');
  await expect(page.locator('.mode-pill')).toHaveText('SERVER SIMULATION');
  await expect(page.getByText('Flask engine connected')).toBeVisible();
  await page.getByRole('button', { name: 'Connect bench', exact: true }).click();
  await expect(page.locator('.inspector .status')).toHaveText('connected');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText('running');
  await page.reload();
  await expect(page.locator('.result-heading .status')).toHaveText('passed', {timeout:10000});
  await page.getByLabel('Fault injection').selectOption('out-of-range');
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText('failed', {timeout:10000});
  await expect(page.locator('.step-failed')).toContainText('outside expected');
  await page.getByRole('link', {name:'Results',exact:true}).click();
  await expect(page.locator('tbody tr')).toHaveCount(2);
});
test('server control test verifies and restores state; cancel is an API operation', async ({ page }) => {
  await page.goto('/overview');
  await expect(page.getByText('Flask engine connected')).toBeVisible();
  await page.getByRole('button', {name:'Connect bench',exact:true}).click();
  await page.getByLabel('Target device').selectOption({label:'Intake valve'});
  await page.getByLabel('Test plan').selectOption('control');
  await page.getByRole('button', {name:'Run test',exact:true}).click();
  await expect(page.locator('.result-heading .status')).toHaveText('passed', {timeout:10000});
  await expect(page.locator('.inspect-reading')).toContainText('0%');
  await page.getByRole('button', {name:'Run test',exact:true}).click();
  await expect(page.locator('.result-heading .status')).toHaveText('running');
  await page.getByRole('button', {name:'Stop test',exact:true}).click();
  await expect(page.locator('.result-heading .status')).toHaveText('cancelled');
});
test('a backend outage is visible and never silently falls back to simulated success', async ({ page }) => {
  await page.goto('/settings');
  await expect(page.getByText('Flask engine connected')).toBeVisible();
  await page.route('**/api/lab', route => route.abort());
  await expect(page.locator('.backend-warning')).toBeVisible({timeout:12000});
  await page.getByRole('link', {name:'Overview',exact:true}).click();
  await expect(page.getByRole('button', {name:'Connect bench',exact:true})).toBeDisabled();
});
