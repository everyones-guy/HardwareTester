import { readFile } from 'node:fs/promises';
import { expect, test, type Locator } from '@playwright/test';

function inputFile(locator: Locator, name: string, payload: unknown) {
  return locator.setInputFiles({
    name,
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify(payload)),
  });
}

test('Pi Workbench compares captures and exports a pinned provisioning plan', async ({ page }) => {
  const capture = {
    schemaVersion: 2,
    capturedAt: '2026-01-10T13:30:00Z',
    model: 'Raspberry Pi 3 Model B Rev 1.2',
    architecture: 'aarch64',
    kernel: '6.18.50+rpt-rpi-v8',
    osId: 'debian',
    osVersion: '13',
    memoryMiB: 921,
    interfaces: ['usb'],
    observations: {
      firmware: { videoCoreRevision: 'a'.repeat(40), startElfSha256: 'a'.repeat(64) },
      configuration: { bootConfigSha256: 'a'.repeat(64), bootCmdlineSha256: 'a'.repeat(64) },
      services: {
        'NetworkManager.service': null,
        'mosquitto.service': {
          loadState: 'not-found',
          activeState: 'inactive',
          unitFileState: null,
        },
        'ssh.service': { loadState: 'loaded', activeState: 'inactive', unitFileState: 'enabled' },
      },
    },
  };
  await page.goto('/pi');
  await expect(page.getByText('Flask engine connected')).toBeVisible();
  const importCapture = async (name: string, data: typeof capture) => {
    await page.getByLabel('Inventory name').fill(name);
    await inputFile(page.getByLabel('Inventory JSON file'), 'capture.json', data);
    await page.getByRole('button', { name: 'Import inventory' }).click();
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  };
  await importCapture('Baseline lab Pi', capture);
  const after = structuredClone(capture);
  after.capturedAt = '2026-01-10T13:31:00Z';
  after.observations.services['ssh.service'].activeState = 'active';
  after.observations.configuration.bootConfigSha256 = 'b'.repeat(64);
  await importCapture('Updated lab Pi', after);
  await expect(page.getByRole('heading', { name: 'Provisioning and drift' })).toHaveCount(1);
  await page.getByLabel('Baseline capture from the same Pi').selectOption({ index: 1 });
  await page.getByRole('button', { name: 'Compare captures' }).click();
  const comparison = page.getByLabel('Inventory drift results');
  await expect(comparison).toContainText('2 changed · 1 unavailable');
  await expect(comparison).toContainText('loaded · inactive · enabled → loaded · active · enabled');

  const pin = { sha256: 'c'.repeat(64), sizeBytes: 512 };
  const manifest = {
    schemaVersion: 1,
    profile: 'pi3b-aarch64',
    release: 'Pi 3B lab image',
    os: { id: 'debian', version: '13' },
    artifacts: { 'sd.img': pin, 'kernel8.img': pin, 'bcm2710-rpi-3-b.dtb': pin },
    bootstrap: {
      'deployment/raspberry-pi/bootstrap.sh': pin,
      'backend/tools/capture_pi_inventory.py': pin,
      'backend/tools/pi_provisioning.py': pin,
    },
    boot: { rootDevice: '/dev/mmcblk0p2', readyMarker: 'READY', timeoutSeconds: 20 },
  };
  await inputFile(page.getByLabel('Approved release manifest'), 'manifest.json', manifest);
  await page.getByRole('button', { name: 'Generate provisioning plan' }).click();
  await expect(page.getByText(/Pi 3B lab image · Plan ready/)).toBeVisible();
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download plan' }).click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toBe('pi3b-provisioning-plan.json');
  const downloaded = JSON.parse(await readFile(await download.path(), 'utf8'));
  expect(downloaded).toMatchObject(manifest);
  expect(downloaded.target).toEqual({
    model: capture.model,
    architecture: capture.architecture,
    capturedAt: after.capturedAt,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
  ).toBeTruthy();
});
