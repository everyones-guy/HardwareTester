import { isLabState, LabState } from './simulator';
import { csrfToken } from './Accounts';
export interface Peripheral {
  id: string;
  name: string;
  type: string;
  device_id: string;
  properties: Record<string, unknown>;
  version: number;
}
export interface Blueprint {
  id: string;
  name: string;
  description: string;
  configuration: Record<string, unknown>;
  devices: { name: string; kind: string }[];
  warnings: string[];
}
export interface UiSourceLocation {
  path: string;
  line: number;
  table: string;
}
export interface PlanStep {
  name: string;
  action:
    | 'read'
    | 'set'
    | 'assert_range'
    | 'assert_equal'
    | 'wait'
    | 'ui_navigate'
    | 'ui_input'
    | 'ui_confirm';
  uiAction?: {
    controlId: string;
    source: UiSourceLocation;
    pageId?: string;
    pageSource?: UiSourceLocation;
  };
  timeout?: number;
  value?: number;
  tolerance?: number;
  min?: number;
  max?: number;
  seconds?: number;
}
export interface SavedPlan {
  id: string;
  name: string;
  description: string;
  kind: 'temperature' | 'valve' | 'relay';
  version: number;
  steps: PlanStep[];
  uiSource?: UiPlanSource;
}
export interface UiPlanSource {
  catalogSha256: string;
  controlId: string;
  handler: string;
  bindingReference: string;
  source: UiSourceLocation;
  stepsSha256: string;
}
export interface SuiteCase {
  name: string;
  scenarioId: string;
  expected: ('passed' | 'failed')[];
}
export interface ValidationSuite {
  id: string;
  version: number;
  name: string;
  description: string;
  kind: 'temperature' | 'valve' | 'relay';
  planId: string;
  cases: SuiteCase[];
}
export interface SuiteRun {
  id: string;
  suite: ValidationSuite;
  plan: { id: string; name: string; version: number };
  device: import('./simulator').Device;
  startedAt: string;
  finishedAt?: string;
  status: 'running' | 'passed' | 'failed' | 'cancelled' | 'error';
  detail?: string;
  restoration?: string;
  cases: (SuiteCase & {
    status: string;
    scenario: import('./ScenarioLibrary').Scenario;
    runId?: string;
    attempts: {
      expected: 'passed' | 'failed';
      matched: boolean;
      run: import('./simulator').TestRun;
    }[];
  })[];
}
export interface ServerResponse {
  suiteId?: string;
  suiteRunId?: string;
  scenarioId?: string;
  planId?: string;
  state: LabState;
  deviceId?: string;
  runId?: string;
  blueprintId?: string;
  preview?: Blueprint;
  capabilities?: { hardware: boolean };
}
function labAuthorization() {
  const token = sessionStorage.getItem('hardware-tester.api-token');
  return token ? { Authorization: `Bearer ${token}` } : undefined;
}

async function requestLab<T>(path = '', method = 'GET', data?: unknown): Promise<T> {
  const multipart = data instanceof FormData;
  const response = await fetch(`/api/lab${path}`, {
    method,
    credentials: 'same-origin',
    headers: {
      ...(method !== 'GET'
        ? {
            ...(!multipart ? { 'Content-Type': 'application/json' } : {}),
            'X-CSRF-Token': csrfToken(),
          }
        : {}),
      ...labAuthorization(),
    },
    body: multipart ? data : data === undefined ? undefined : JSON.stringify(data),
    signal: AbortSignal.timeout(multipart || path.startsWith('/workspace/') ? 60000 : 10000),
  });
  const payload = await response.json().catch(() => {
    throw new Error('Backend returned an invalid response. Check that Flask is running.');
  });
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('ht-auth-changed'));
    throw new Error(payload.error || `Backend request failed (${response.status}).`);
  }
  return payload;
}
export async function labRequest(
  path = '',
  method = 'GET',
  data?: unknown,
): Promise<ServerResponse> {
  const payload = await requestLab<ServerResponse>(path, method, data);
  if (!isLabState(payload.state)) throw new Error('Backend returned an incompatible workspace.');
  return payload;
}
export interface WorkspaceArchive {
  format: 'hardware-tester-workspace';
  version: 1;
  exportedAt: string;
  workspace: Record<string, unknown[]>;
}
export interface BackupPreview {
  revision: number;
  digest: string;
  added: number;
  warnings: string[];
  rows: {
    collection: string;
    incoming: number;
    added: number;
    copied: number;
    skipped: number;
    trimmed: number;
    conflicts: { name: string; existingName: string }[];
  }[];
}
export const workspaceRequest = requestLab;

export async function fetchFirmwareBinary(digest: string): Promise<Blob> {
  const response = await fetch(`/api/lab/firmware/${encodeURIComponent(digest)}/binary`, {
    headers: labAuthorization(),
    signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('ht-auth-changed'));
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `Firmware download failed (${response.status}).`);
  }
  return response.blob();
}
export function savedBackendMode(): boolean {
  try {
    return (
      localStorage.getItem('hardware-tester.engine') === 'server' ||
      (localStorage.getItem('hardware-tester.engine') === null &&
        import.meta.env.VITE_LAB_MODE === 'server')
    );
  } catch {
    return import.meta.env.VITE_LAB_MODE === 'server';
  }
}
