import { test, expect } from '@playwright/test';

test('suite catalog and editor collapse, filter, page, and preserve drafts', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  const ids: string[] = [];
  for (let i = 1; i <= 7; i++) {
    const r = await request.post('/api/lab/validation-suites', {
      data: {
        name: `Suite catalog ${i}`,
        description: 'Repeatable bench checks',
        kind: 'temperature',
        planId: 'smoke',
        cases: Array.from({ length: i === 1 ? 10 : 1 }, (_, n) => ({
          name: `Check ${n + 1}`,
          scenarioId: 'preset-healthy',
          expected: i === 2 ? ['failed', 'passed'] : ['passed'],
        })),
      },
    });
    expect(r.ok()).toBeTruthy();
    ids.push((await r.json()).suiteId);
  }
  try {
    await page.goto('/suites');
    const library = page.getByRole('region', { name: 'Saved validation suites' });
    const editor = page.getByRole('region', { name: 'Suite editor' });
    await library.getByLabel('Search suites').fill('Suite catalog');
    await library.getByLabel('Visible suite cards').selectOption('2');
    await expect(library.locator('.suite-catalog-card')).toHaveCount(2);
    const first = library.getByRole('button', {
      name: 'Validation suite Suite catalog 1',
      exact: true,
    });
    await first.focus();
    await page.keyboard.press('Enter');
    await expect(first).toHaveAttribute('aria-expanded', 'true');
    await expect(library.locator('.suite-case-index li')).toHaveCount(10);
    await library.getByRole('button', { name: 'Collapse saved suites' }).click();
    await expect(first).toBeHidden();
    await library.getByRole('button', { name: 'Expand saved suites' }).click();
    await expect(first).toHaveAttribute('aria-expanded', 'true');
    await library.getByRole('button', { name: 'Next suite page' }).click();
    await expect(
      library.getByRole('button', { name: 'Validation suite Suite catalog 3', exact: true }),
    ).toBeVisible();
    await library.getByLabel('Filter suite expectations').selectOption('recovery');
    await expect(library.locator('.suite-catalog-card')).toHaveCount(1);
    await library.getByLabel('Filter suite expectations').selectOption('all');
    await library.getByLabel('Search suites').fill('Suite catalog 1');
    await first.click();
    await library.getByRole('button', { name: 'Edit', exact: true }).click();
    await expect(editor.locator('.suite-case-row')).toHaveCount(10);
    await expect(editor.locator('fieldset')).toHaveCount(0);
    await editor.getByRole('button', { name: 'Edit case 2: Check 2', exact: true }).click();
    await editor.getByLabel('Case 2 name', { exact: true }).fill('');
    await editor.getByRole('button', { name: 'Collapse all cases' }).click();
    await expect(editor.getByRole('alert')).toContainText('Give this case a name.');
    await expect(editor.getByRole('button', { name: 'Save suite changes' })).toBeDisabled();
    await editor.getByRole('button', { name: 'Edit case 2: Unnamed case', exact: true }).click();
    await editor.getByLabel('Case 2 name', { exact: true }).fill('Moved check');
    await editor.getByRole('button', { name: 'Move case 2 up', exact: true }).click();
    await expect(editor.getByLabel('Case 1 name', { exact: true })).toHaveValue('Moved check');
    await editor.getByRole('button', { name: 'Remove case 1', exact: true }).click();
    await editor.getByRole('button', { name: 'Add case', exact: true }).click();
    await editor.getByLabel('Case 10 name', { exact: true }).fill('Draft retained');
    await editor.getByRole('button', { name: 'Collapse suite editor' }).click();
    await expect(editor.getByLabel('Suite name', { exact: true })).toBeHidden();
    await editor.getByRole('button', { name: 'Expand suite editor' }).click();
    await expect(editor.getByLabel('Case 10 name', { exact: true })).toHaveValue('Draft retained');
    await editor.getByLabel('Suite name', { exact: true }).fill('Z polished suite');
    await library.getByRole('button', { name: 'Collapse saved suites' }).click();
    await editor.getByRole('button', { name: 'Save suite changes' }).click();
    await expect(
      library.getByRole('button', { name: 'Validation suite Z polished suite', exact: true }),
    ).toHaveAttribute('aria-expanded', 'true');
    await expect(library.getByLabel('Search suites')).toHaveValue('');
    await expect(library).toContainText('v2');
    await expect(library).toContainText('Draft retained');
    await editor.getByRole('button', { name: 'Collapse all cases' }).click();
    if (process.env.LAB_SCREENSHOT_DIR) {
      await page.setViewportSize({ width: 1600, height: 1100 });
      await page.locator('.suite-management-grid').screenshot({
        path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-suite-library.png`,
      });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
  } finally {
    const state = (await (await request.get('/api/lab')).json()).state;
    for (const id of ids) {
      const suite = state.validationSuites.find((s: { id: string }) => s.id === id);
      if (suite)
        await request.delete(`/api/lab/validation-suites/${id}`, {
          data: { version: suite.version },
        });
    }
  }
});
