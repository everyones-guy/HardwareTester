import { test, expect } from '@playwright/test';

test('account index supports filtering, paging, keyboard expansion and narrow screens', async ({
  page,
}) => {
  await page.goto('/settings');
  await page.getByLabel('Sign in username').fill('browser-admin');
  await page.getByLabel('Sign in password').fill('Browser-test-passphrase-123');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'User accounts', exact: true })).toBeVisible();
  const session = await (await page.request.get('/api/auth/session')).json();
  const existing = (await (await page.request.get('/api/auth/users')).json()).users;
  for (let i = 1; i <= 6; i++) {
    const username = `directory-test-${i}`;
    if (!existing.some((u: { username: string }) => u.username === username)) {
      expect(
        (
          await page.request.post('/api/auth/users', {
            headers: { 'X-CSRF-Token': session.csrf },
            data: {
              username,
              email: `record${i}@example.com`,
              password: 'Directory-test-password-123',
              role: i % 2 ? 'viewer' : 'operator',
            },
          })
        ).ok(),
      ).toBeTruthy();
    }
  }
  await page.reload();
  const directory = page.locator('.user-directory');
  await page.getByLabel('Search accounts').fill('directory-test');
  await page.getByLabel('Visible account rows').selectOption('2');
  await expect(directory.locator('.directory-card')).toHaveCount(2);
  const row = page.getByRole('button', { name: 'Account directory-test-1', exact: true });
  await row.focus();
  await page.keyboard.press('Enter');
  await expect(row).toHaveAttribute('aria-expanded', 'true');
  await expect(directory.getByText('record1@example.com', { exact: true }).last()).toBeVisible();
  await expect(page.getByLabel('Password for directory-test-1')).toHaveCount(0);
  await directory.getByRole('button', { name: 'Reset password', exact: true }).click();
  await expect(page.getByLabel('Password for directory-test-1')).toBeVisible();
  await page.getByRole('button', { name: 'Account directory-test-2', exact: true }).click();
  await expect(row).toHaveAttribute('aria-expanded', 'false');
  await expect(page.getByLabel('Password for directory-test-1')).toHaveCount(0);
  await page.getByRole('button', { name: 'Next account page' }).click();
  await expect(
    page.getByRole('button', { name: 'Account directory-test-3', exact: true }),
  ).toBeVisible();
  await expect(directory.locator('.directory-details')).toHaveCount(0);
  await page
    .getByRole('group', { name: 'Filter accounts by role' })
    .getByRole('button', { name: /Viewer/ })
    .click();
  await expect(directory.locator('.directory-role')).toHaveText(['viewer', 'viewer']);
  await page.getByLabel('Search accounts').fill('no-matching-account');
  await expect(directory.getByRole('heading', { name: 'No accounts match' })).toBeVisible();
  await directory.getByRole('button', { name: 'Clear filters' }).click();
  await page.getByLabel('Search accounts').fill('directory-test');
  await page.getByLabel('Visible account rows').selectOption('5');
  await page.getByRole('button', { name: 'Account directory-test-1', exact: true }).click();
  await directory.screenshot({
    path: 'C:/Users/Gary/Documents/Codex/2026-10-05/i-v/outputs/hardware-tester-user-directory.png',
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await directory.scrollIntoViewIfNeeded();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBeTruthy();
  await expect(
    directory.getByRole('button', { name: 'Reset password', exact: true }),
  ).toBeVisible();
});
