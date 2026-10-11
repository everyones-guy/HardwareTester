import { test, expect } from '@playwright/test';

test('Flask baseline persists through reload and compares a rerun', async ({ page, request }) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  await page.goto('/overview');
  await expect(page.getByText('Flask engine connected')).toBeVisible();
  await page.getByRole('button', { name: 'Connect bench', exact: true }).click();
  await page.getByRole('button', { name: 'Run test', exact: true }).click();
  await expect(page.locator('.result-heading .status')).toHaveText('passed', { timeout: 10000 });
  await page.getByRole('link', { name: 'Results', exact: true }).click();
  const analysis = page.getByRole('region', { name: 'Result comparison and trends' });
  await analysis.getByRole('button', { name: 'Use this run as baseline' }).click();
  await expect(analysis.getByRole('button', { name: 'Clear baseline' })).toBeEnabled();
  const state = (await (await request.get('/api/lab')).json()).state;
  const baseline = state.runs.find((r: { baseline?: boolean }) => r.baseline);
  expect(baseline.status).toBe('passed');
  await page.reload();
  await expect(analysis.getByRole('button', { name: 'Clear baseline' })).toBeEnabled();
  await page
    .getByRole('region', { name: 'Run report' })
    .getByRole('button', { name: 'Rerun test' })
    .click();
  await expect(page.locator('.report-verdict')).toHaveText('passed', { timeout: 10000 });
  await expect(analysis.getByLabel('Reference run')).toHaveValue(baseline.id);
  await expect(analysis).toContainText('Matching recorded configuration');
  await expect(analysis).toContainText('0 checks regressed');
  await expect(analysis.getByRole('img', { name: /History trend: 2 readings/ })).toBeVisible();
});
