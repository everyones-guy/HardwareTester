import type { LabState, TestRun, TestStep } from './simulator';

export function planKey(run: TestRun): string {
  return (
    run.configuration?.plan.id ??
    run.planId ??
    { 'Connection & health': 'smoke', 'Control response': 'control' }[run.plan] ??
    run.plan
  );
}
export const sameSeries = (a: TestRun, b: TestRun) =>
  a.deviceId === b.deviceId && planKey(a) === planKey(b);
export const eligibleBaseline = (run: TestRun) =>
  run.status === 'passed' && !!run.finishedAt && run.restoration !== 'failed';
export function markBaseline(state: LabState, id: string, enabled: boolean): LabState {
  const run = state.runs.find((r) => r.id === id);
  if (!run || (enabled && !eligibleBaseline(run)))
    throw new Error('Choose a completed passing run.');
  return {
    ...state,
    runs: state.runs.map((r) =>
      r.id === id
        ? { ...r, baseline: enabled }
        : enabled && sameSeries(r, run)
          ? { ...r, baseline: false }
          : r,
    ),
  };
}
function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object')
    return JSON.stringify(
      Object.fromEntries(
        Object.entries(value)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([k, v]) => [k, stable(v)]),
      ),
    );
  return JSON.stringify(value) ?? 'undefined';
}
export function configurationChanges(a: TestRun, b: TestRun): string[] {
  const ac = a.configuration,
    bc = b.configuration;
  if (!ac || !bc) return ['Configuration not recorded'];
  const changes: string[] = [];
  if (stable(ac.plan) !== stable(bc.plan)) changes.push('Plan version or steps');
  for (const [key, label] of [
    ['kind', 'Device profile'],
    ['adapter', 'Transport adapter'],
    ['protocol', 'Protocol'],
    ['endpoint', 'Endpoint'],
    ['baudrate', 'Baud rate'],
    ['fault', 'Injected fault'],
    ['scenario', 'Emulator scenario'],
    ['scenarioCursor', 'Scenario starting position'],
    ['enabled', 'Initial output state'],
  ] as const) {
    if (stable(ac.device[key]) !== stable(bc.device[key])) changes.push(label);
  }
  // Ignore peripheral array order while retaining IDs, properties and versions.
  const peripherals = (c: typeof ac) => [...c.peripherals].sort((x, y) => x.id.localeCompare(y.id));
  if (stable(peripherals(ac)) !== stable(peripherals(bc))) changes.push('Attached peripherals');
  const writes =
    ac.plan.id === 'control' ||
    bc.plan.id === 'control' ||
    [...ac.plan.steps, ...bc.plan.steps].some((s) => typeof s === 'object' && s.action === 'set');
  if (writes && a.originalValue !== b.originalValue) changes.push('Initial output value');
  return changes;
}
export function elapsedMs(run: TestRun): number | undefined {
  if (!run.finishedAt) return undefined;
  const value = Date.parse(run.finishedAt) - Date.parse(run.startedAt);
  return Number.isFinite(value) && value >= 0 ? value : undefined;
}
export function expectedRange(step?: TestStep): [number, number] | undefined {
  const e = step?.expected;
  const low = e?.min ?? (e?.value === undefined ? undefined : e.value - (e.tolerance ?? 0));
  const high = e?.max ?? (e?.value === undefined ? undefined : e.value + (e.tolerance ?? 0));
  return low !== undefined &&
    high !== undefined &&
    Number.isFinite(low) &&
    Number.isFinite(high) &&
    low <= high
    ? [low, high]
    : undefined;
}
export function matchingStep(a: TestRun, b: TestRun, index: number): boolean {
  const action = (r: TestRun) => {
    const definitions = r.configuration?.plan.steps;
    if (!definitions?.length || typeof definitions[0] === 'string') return r.steps[index]?.name;
    if (index === 0) return 'handshake';
    const step = definitions[index - 1];
    return step && typeof step === 'object' ? step.action : 'restore';
  };
  return (
    !!a.configuration &&
    !!b.configuration &&
    !!a.steps[index] &&
    !!b.steps[index] &&
    a.steps[index].name === b.steps[index].name &&
    action(a) === action(b) &&
    a.configuration?.device.kind === b.configuration?.device.kind
  );
}
export const numeric = (value: number | undefined): value is number =>
  value !== undefined && Number.isFinite(value);
