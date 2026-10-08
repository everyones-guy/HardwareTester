import { test, expect } from '@playwright/test';
const password = 'Browser-test-passphrase-123';
test('admin onboarding, viewer enforcement, role changes, session revocation, and build identity', async ({
  page,
  browser,
}) => {
  test.setTimeout(60000);
  await page.goto('/settings');
  const setup = (await (await page.request.get('/api/auth/session')).json()).setupRequired;
  await page.getByLabel('Sign in username').fill('browser-admin');
  await page.getByLabel('Sign in password').fill(password);
  if (setup) await page.getByLabel('Admin email').fill('browser-admin@example.com');
  await page.getByRole('button', { name: setup ? 'Create admin' : 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'User accounts', exact: true })).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Environment and build', exact: true }),
  ).toBeVisible();
  const auth = await (await page.request.get('/api/auth/session')).json();
  await page.request.post('/api/lab/runs/cancel', {
    headers: { 'X-CSRF-Token': auth.csrf },
    data: {},
  });
  expect(
    (
      await page.request.post('/api/lab/reset', {
        headers: { 'X-CSRF-Token': auth.csrf },
        data: {},
      })
    ).ok(),
  ).toBeTruthy();
  const users = await (await page.request.get('/api/auth/users')).json();
  let viewer = users.users.find((u: { username: string }) => u.username === 'browser-viewer');
  if (!viewer) {
    await page.getByRole('button', { name: 'New account', exact: true }).click();
    await page.getByLabel('New username', { exact: true }).fill('browser-viewer');
    await page.getByLabel('New user email').fill('viewer@example.com');
    await page.getByLabel('New user password').fill(password);
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'browser-viewer', exact: true })).toBeVisible();
    viewer = (await (await page.request.get('/api/auth/users')).json()).users.find(
      (u: { username: string }) => u.username === 'browser-viewer',
    );
  } else {
    await page.request.patch(`/api/auth/users/${viewer.id}`, {
      headers: { 'X-CSRF-Token': auth.csrf },
      data: { version: viewer.version, role: 'viewer', enabled: true, password },
    });
  }
  const context = await browser.newContext();
  const viewerPage = await context.newPage();
  await viewerPage.goto('http://127.0.0.1:5175/overview');
  await viewerPage.getByLabel('Sign in username').fill('browser-viewer');
  await viewerPage.getByLabel('Sign in password').fill(password);
  await viewerPage.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(
    viewerPage.getByRole('button', { name: 'Connect bench', exact: true }),
  ).toBeDisabled();
  await expect(viewerPage.getByRole('button', { name: 'Add device', exact: true })).toBeDisabled();
  const viewerAuth = await (await viewerPage.request.get('/api/auth/session')).json();
  expect(
    (
      await viewerPage.request.post('/api/lab/connect-bench', {
        headers: { 'X-CSRF-Token': viewerAuth.csrf },
        data: {},
      })
    ).status(),
  ).toBe(403);
  await page.reload();
  await page.getByRole('button', { name: 'Account browser-viewer', exact: true }).click();
  await page.getByLabel('Role for browser-viewer').selectOption('operator');
  await expect(viewerPage.getByRole('button', { name: 'Connect bench', exact: true })).toBeEnabled({
    timeout: 10000,
  });
  await viewerPage.getByRole('button', { name: 'Connect bench', exact: true }).click();
  await expect(viewerPage.locator('.inspector .status')).toHaveText('connected');
  await expect(viewerPage.getByRole('button', { name: 'Add device', exact: true })).toBeDisabled();
  await viewerPage.getByRole('link', { name: 'Workspace settings', exact: true }).click();
  await expect(viewerPage.getByText(/Signed in as/)).toContainText('operator');
  const account = page
    .locator('.directory-card')
    .filter({ has: page.getByRole('heading', { name: 'browser-viewer', exact: true }) });
  page.once('dialog', (dialog) => dialog.accept());
  await account.getByRole('button', { name: 'Disable', exact: true }).click();
  await expect(viewerPage.getByLabel('Sign in username')).toBeVisible({ timeout: 10000 });
  expect((await viewerPage.request.get('/api/lab')).status()).toBe(401);
  await context.close();
});
