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
export interface PlanStep {
  name: string;
  action: 'read' | 'set' | 'assert_range' | 'assert_equal' | 'wait';
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
export async function labRequest(
  path = '',
  method = 'GET',
  data?: unknown,
): Promise<ServerResponse> {
  const token = sessionStorage.getItem('hardware-tester.api-token');
  const response = await fetch(`/api/lab${path}`, {
    method,
    credentials: 'same-origin',
    headers: {
      ...(method !== 'GET'
        ? { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken() }
        : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: data === undefined ? undefined : JSON.stringify(data),
    signal: AbortSignal.timeout(10000),
  });
  const payload = await response.json().catch(() => {
    throw new Error('Backend returned an invalid response. Check that Flask is running.');
  });
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('ht-auth-changed'));
    throw new Error(payload.error || `Backend request failed (${response.status}).`);
  }
  if (!isLabState(payload.state)) throw new Error('Backend returned an incompatible workspace.');
  return payload;
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
