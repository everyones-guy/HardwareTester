import type { Scenario } from './ScenarioLibrary';
export type DeviceKind = 'temperature' | 'valve' | 'relay';
export type Fault = 'none' | 'timeout' | 'out-of-range';
export interface ConnectionCheck {
  checkedAt: string;
  status: 'passed' | 'warning' | 'failed';
  detail: string;
  durationMs: number;
  value: number | null;
}
export interface Device {
  scenario?: Scenario | null;
  scenarioCursor?: number;
  scenarioOutput?: number;
  lastContactAt?: string | null;
  diagnostics?: ConnectionCheck[];
  adapter?: 'simulation' | 'serial' | 'mqtt';
  baudrate?: number;
  lastError?: string | null;
  safetyWarning?: string | null;
  id: string;
  name: string;
  kind: DeviceKind;
  protocol: 'MQTT' | 'Serial' | 'USB';
  endpoint: string;
  connected: boolean;
  fault: Fault;
  value: number;
  enabled: boolean;
}
export interface TestStep {
  name: string;
  status: 'pending' | 'passed' | 'failed';
  detail: string;
  observed?: number;
  startedAt?: string;
  durationMs?: number;
  expected?: { min?: number; max?: number; value?: number; tolerance?: number };
  finishedAt?: string;
}
export interface TestRun {
  restoration?: string;
  planId?: string;
  configuration?: {
    device: Device;
    peripherals: import('./backend').Peripheral[];
    plan: {
      id: string;
      version: number;
      name: string;
      steps: (string | import('./backend').PlanStep)[];
    };
    workspaceRevision: number;
  };
  id: string;
  deviceId: string;
  deviceName: string;
  plan: string;
  startedAt: string;
  finishedAt?: string;
  status: 'running' | 'passed' | 'failed' | 'cancelled';
  steps: TestStep[];
  originalValue?: number;
  originalEnabled?: boolean;
}
export interface LogEntry {
  deviceId?: string | null;
  runId?: string | null;
  id: string;
  time: string;
  level: 'info' | 'error' | 'success';
  message: string;
}
export interface LabState {
  scenarios?: Scenario[];
  version: 1;
  devices: Device[];
  runs: TestRun[];
  logs: LogEntry[];
  revision?: number;
  peripherals?: import('./backend').Peripheral[];
  blueprints?: import('./backend').Blueprint[];
  testPlans?: import('./backend').SavedPlan[];
}
export const profiles: Record<
  DeviceKind,
  { name: string; protocol: Device['protocol']; endpoint: string; unit: string }
> = {
  temperature: {
    name: 'Temperature sensor',
    protocol: 'MQTT',
    endpoint: 'sim://mqtt/lab/temperature',
    unit: '°C',
  },
  valve: {
    name: 'Proportional valve',
    protocol: 'Serial',
    endpoint: 'sim://serial/COM-DEMO',
    unit: '%',
  },
  relay: { name: 'Relay controller', protocol: 'USB', endpoint: 'sim://usb/relay-01', unit: '' },
};
export const uid = () => crypto.randomUUID();
export function createDevice(kind: DeviceKind, name = profiles[kind].name): Device {
  return {
    id: uid(),
    name,
    kind,
    protocol: profiles[kind].protocol,
    endpoint: profiles[kind].endpoint,
    connected: false,
    fault: 'none',
    value: kind === 'temperature' ? 24 : 0,
    enabled: false,
  };
}
export function initialState(): LabState {
  return {
    version: 1,
    devices: [
      createDevice('temperature', 'Ambient temperature'),
      createDevice('valve', 'Intake valve'),
      createDevice('relay', 'Pump relay'),
    ],
    runs: [],
    logs: [],
  };
}
export function logEntry(message: string, level: LogEntry['level'] = 'info'): LogEntry {
  return { id: uid(), time: new Date().toISOString(), level, message };
}
export function telemetry(device: Device, tick: number): number {
  if (device.fault === 'out-of-range') return device.kind === 'temperature' ? 95 : 150;
  if (device.kind === 'temperature') return Math.round((24 + Math.sin(tick / 4) * 1.4) * 10) / 10;
  return device.value;
}
export const planNames = { smoke: 'Connection & health', control: 'Control response' } as const;
export type Plan = keyof typeof planNames;
export function createRun(device: Device, plan: Plan): TestRun {
  const names =
    plan === 'smoke'
      ? ['Connection handshake', 'Read telemetry', 'Validate operating range']
      : [
          'Connection handshake',
          'Send control command',
          'Verify response',
          'Restore initial state',
        ];
  return {
    id: uid(),
    deviceId: device.id,
    deviceName: device.name,
    plan: planNames[plan],
    planId: plan,
    configuration: {
      device: { ...device },
      peripherals: [],
      plan: { id: plan, version: 1, name: planNames[plan], steps: names },
      workspaceRevision: 0,
    },
    startedAt: new Date().toISOString(),
    status: 'running',
    originalValue: device.value,
    originalEnabled: device.enabled,
    steps: names.map((name) => ({ name, status: 'pending', detail: 'Waiting to execute' })),
  };
}
// Each check reads current state. A disconnect or fault during a run is observable.
export function evaluateStep(device: Device | undefined, name: string): TestStep {
  const fail = (detail: string): TestStep => ({ name, status: 'failed', detail });
  if (!device?.connected) return fail('Device disconnected. Connect the device and retry.');
  if (device.fault === 'timeout')
    return fail('Simulated transport timeout: no acknowledgement received.');
  if (name === 'Validate operating range' || name === 'Verify response') {
    const max = device.kind === 'temperature' ? 50 : device.kind === 'valve' ? 100 : 1;
    if (!Number.isFinite(device.value) || device.value < 0 || device.value > max)
      return fail(`Reading ${device.value} is outside expected range 0–${max}.`);
  }
  return {
    name,
    status: 'passed',
    detail:
      name === 'Connection handshake'
        ? `${device.protocol} simulator acknowledged connection.`
        : name === 'Read telemetry'
          ? `Received ${device.value}${profiles[device.kind].unit}.`
          : name === 'Validate operating range'
            ? `Reading ${device.value}${profiles[device.kind].unit} is within the operating range.`
            : name === 'Verify response'
              ? `Observed expected response: ${device.value}${profiles[device.kind].unit}.`
              : name === 'Restore initial state'
                ? `Restored ${device.value}${profiles[device.kind].unit}.`
                : 'Simulator acknowledged command.',
  };
}
export function controlValue(device: Device): number {
  return device.kind === 'temperature' ? 30 : device.kind === 'valve' ? 75 : 1;
}
export function finishRun(run: TestRun, cancelled = false): TestRun {
  return {
    ...run,
    finishedAt: new Date().toISOString(),
    status: cancelled
      ? 'cancelled'
      : run.steps.length > 0 && run.steps.every((s) => s.status === 'passed')
        ? 'passed'
        : 'failed',
  };
}
const key = 'hardware-tester.lab.v1';
export function saveState(state: LabState): boolean {
  try {
    localStorage.setItem(key, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}
export function loadState(): LabState {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return initialState();
    const parsed: unknown = JSON.parse(raw);
    if (!isLabState(parsed)) return initialState();
    return {
      ...parsed,
      devices: parsed.devices.map((d) => {
        const interrupted = parsed.runs.find((r) => r.deviceId === d.id && r.status === 'running');
        return {
          ...d,
          connected: false,
          value: interrupted?.originalValue ?? d.value,
          enabled: interrupted?.originalEnabled ?? d.enabled,
        };
      }),
      runs: parsed.runs.map((r) => (r.status === 'running' ? finishRun(r, true) : r)),
    };
  } catch {
    return initialState();
  }
}
export function isLabState(input: unknown): input is LabState {
  if (!input || typeof input !== 'object') return false;
  const s = input as LabState;
  return (
    s.version === 1 &&
    Array.isArray(s.devices) &&
    s.devices.length <= 100 &&
    s.devices.every(
      (d) =>
        typeof d?.id === 'string' &&
        typeof d.name === 'string' &&
        d.name.length <= 100 &&
        ['temperature', 'valve', 'relay'].includes(d.kind) &&
        ['MQTT', 'Serial', 'USB'].includes(d.protocol) &&
        typeof d.endpoint === 'string' &&
        typeof d.connected === 'boolean' &&
        ['none', 'timeout', 'out-of-range'].includes(d.fault) &&
        Number.isFinite(d.value) &&
        typeof d.enabled === 'boolean',
    ) &&
    new Set(s.devices.map((d) => d.id)).size === s.devices.length &&
    Array.isArray(s.runs) &&
    s.runs.every(
      (r) =>
        typeof r?.id === 'string' &&
        typeof r.deviceId === 'string' &&
        typeof r.deviceName === 'string' &&
        typeof r.plan === 'string' &&
        typeof r.startedAt === 'string' &&
        (r.originalValue === undefined || Number.isFinite(r.originalValue)) &&
        (r.originalEnabled === undefined || typeof r.originalEnabled === 'boolean') &&
        ['running', 'passed', 'failed', 'cancelled'].includes(r.status) &&
        Array.isArray(r.steps) &&
        r.steps.every(
          (step) =>
            typeof step?.name === 'string' &&
            typeof step.detail === 'string' &&
            ['pending', 'passed', 'failed'].includes(step.status),
        ),
    ) &&
    Array.isArray(s.logs) &&
    s.logs.every(
      (l) =>
        typeof l?.id === 'string' &&
        typeof l.time === 'string' &&
        typeof l.message === 'string' &&
        ['info', 'error', 'success'].includes(l.level),
    )
  );
}
