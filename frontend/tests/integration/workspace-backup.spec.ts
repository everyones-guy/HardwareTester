import { test, expect } from '@playwright/test';

test('workspace archive exports, previews conflicts, rejects stale previews, and imports copies', async ({
  page,
  request,
}) => {
  await request.post('/api/lab/runs/cancel', { data: {} });
  await request.post('/api/lab/reset', { data: {} });
  const created = await request.post('/api/lab/test-plans', {
    data: {
      name: 'Archive integration plan',
      kind: 'temperature',
      steps: [{ name: 'Read probe', action: 'read' }],
    },
  });
  const id = (await created.json()).planId;
  const original = (await (await request.get('/api/lab')).json()).state;
  try {
    await page.goto('/settings');
    const backup = page.getByRole('region', { name: 'Workspace backup and restore' });
    await backup.getByRole('button', { name: 'Collapse backup tools' }).click();
    await expect(backup.getByRole('button', { name: 'Download workspace archive' })).toBeHidden();
    await backup.getByRole('button', { name: 'Expand backup tools' }).click();
    const downloading = page.waitForEvent('download');
    await backup.getByRole('button', { name: 'Download workspace archive' }).click();
    const download = await downloading;
    expect(download.suggestedFilename()).toMatch(/^hardware-tester-workspace-.*\.json$/);
    const stream = await download.createReadStream();
    const chunks: Buffer[] = [];
    for await (const chunk of stream!) chunks.push(chunk);
    const file = Buffer.concat(chunks);
    const archive = JSON.parse(file.toString());
    expect(archive.format).toBe('hardware-tester-workspace');
    expect(archive.workspace.testPlans.some((p: { id: string }) => p.id === id)).toBeTruthy();
    expect(archive.workspace.accounts).toBeUndefined();
    await backup
      .getByLabel('Workspace archive file')
      .setInputFiles({ name: 'workspace.json', mimeType: 'application/json', buffer: file });
    await backup.getByLabel('Include archived history').uncheck();
    await backup.getByRole('button', { name: 'Validate & preview import' }).click();
    const preview = backup.getByRole('region', { name: 'Workspace import preview' });
    await expect(preview).toContainText('0 entries to add');
    await expect(backup.getByRole('button', { name: 'Apply workspace import' })).toBeDisabled();
    await backup.getByLabel('Workspace conflict policy').selectOption('copy');
    await expect(preview).toBeHidden();
    await backup.getByRole('button', { name: 'Validate & preview import' }).click();
    await expect(preview).toContainText('imported as copies');
    const reviewState = (await (await request.get('/api/lab')).json()).state;
    expect(reviewState.devices).toHaveLength(original.devices.length);
    await request.post('/api/lab/devices', {
      data: { name: 'Concurrent archive edit', kind: 'relay', adapter: 'simulation' },
    });
    await expect(preview.getByRole('alert')).toContainText('workspace changed');
    await expect(backup.getByRole('button', { name: 'Apply workspace import' })).toBeDisabled();
    await backup.getByRole('button', { name: 'Validate & preview import' }).click();
    if (process.env.LAB_SCREENSHOT_DIR) {
      await page.setViewportSize({ width: 1550, height: 1150 });
      await backup.screenshot({
        path: `${process.env.LAB_SCREENSHOT_DIR}/hardware-tester-workspace-backup.png`,
      });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
    ).toBeTruthy();
    await backup.getByRole('button', { name: 'Apply workspace import' }).click();
    await expect(backup.getByRole('status')).toContainText('Workspace import complete');
    const state = (await (await request.get('/api/lab')).json()).state;
    const copy = state.testPlans.find(
      (p: { name: string }) => p.name === 'Archive integration plan (imported)',
    );
    expect(copy.id).not.toBe(id);
    expect(
      state.devices
        .filter((d: { name: string }) => d.name.endsWith('(imported)'))
        .every((d: { connected: boolean }) => !d.connected),
    ).toBeTruthy();
    await page.reload();
    await expect(backup.getByRole('button', { name: 'Download workspace archive' })).toBeEnabled();
    await backup.getByLabel('Workspace archive file').setInputFiles({
      name: 'invalid.json',
      mimeType: 'application/json',
      buffer: Buffer.from('{"format":"other"}'),
    });
    await expect(backup.getByRole('alert')).toContainText('Hardware Tester workspace archive');
  } finally {
    const state = (await (await request.get('/api/lab')).json()).state;
    for (const p of state.testPlans.filter(
      (p: { id: string }) =>
        !original.testPlans.some((v: { id: string }) => v.id === p.id) || p.id === id,
    ))
      await request.delete(`/api/lab/test-plans/${p.id}`, { data: { version: p.version } });
    for (const d of state.devices.filter(
      (d: { id: string }) => !original.devices.some((v: { id: string }) => v.id === d.id),
    ))
      await request.delete(`/api/lab/devices/${d.id}`, { data: {} });
    for (const s of state.validationSuites.filter(
      (s: { id: string }) => !original.validationSuites.some((v: { id: string }) => v.id === s.id),
    ))
      await request.delete(`/api/lab/validation-suites/${s.id}`, { data: { version: s.version } });
    for (const s of state.scenarios.filter(
      (s: { id: string }) => !original.scenarios.some((v: { id: string }) => v.id === s.id),
    ))
      await request.delete(`/api/lab/scenarios/${s.id}`, { data: { version: s.version } });
    for (const b of state.blueprints.filter(
      (b: { id: string }) => !original.blueprints.some((v: { id: string }) => v.id === b.id),
    ))
      await request.delete(`/api/lab/blueprints/${b.id}`, { data: {} });
  }
});
