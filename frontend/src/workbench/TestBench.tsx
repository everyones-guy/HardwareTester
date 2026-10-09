import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { FiCheck, FiCpu, FiLink, FiPlay, FiSquare, FiX } from 'react-icons/fi';
import { Device, LabState, TestRun, profiles, planNames } from './simulator';
import { ServerResponse } from './backend';
import { ScenarioControls } from './ScenarioLibrary';
import { stepSummary } from './PlanStepRow';
import './test-bench.css';

function SignalMonitor({ device }: { device?: Device }) {
  const [trace, setTrace] = useState<{ id: string; values: number[] }>({ id: '', values: [] });
  useEffect(() => {
    if (!device?.connected || !Number.isFinite(device.value)) return;
    setTrace((old) => ({
      id: device.id,
      values: [...(old.id === device.id ? old.values : []), device.value].slice(-40),
    }));
  }, [device?.id, device?.connected, device?.value, device?.lastContactAt]);
  const values = device?.connected && trace.id === device.id ? trace.values : [];
  const min = Math.min(...values, device?.kind === 'relay' ? 0 : Infinity);
  const max = Math.max(...values, device?.kind === 'relay' ? 1 : -Infinity);
  const pad = Math.max((max - min) * 0.2, device?.kind === 'relay' ? 0.1 : 1);
  const points = values
    .map(
      (v, i) =>
        `${20 + (i / Math.max(1, values.length - 1)) * 460},${135 - ((v - (min - pad)) / (max - min + 2 * pad)) * 110}`,
    )
    .join(' ');
  const reading = !device?.connected
    ? '—'
    : device.kind === 'relay'
      ? device.value
        ? 'ON'
        : 'OFF'
      : String(device.value);
  return (
    <section className="bench-display" aria-label="Signal monitor">
      <header>
        <span>INPUT / {device ? profiles[device.kind].name : 'NO DEVICE'}</span>
        <span>{device?.connected ? 'CONNECTED' : 'NO CONNECTION'}</span>
      </header>
      <div className="bench-reading">
        <strong>{reading}</strong>
        <span>
          {device?.kind === 'relay' ? 'RELAY STATE' : device ? profiles[device.kind].unit : ''}
        </span>
        <small>
          {device?.adapter && device.adapter !== 'simulation'
            ? device.adapter.toUpperCase()
            : 'SIMULATED INPUT'}
        </small>
      </div>
      <svg
        viewBox="0 0 500 160"
        role="img"
        aria-label={
          values.length
            ? `${values.length} received readings; minimum ${min}, maximum ${max}`
            : 'Waiting for connected device readings'
        }
      >
        {Array.from({ length: 11 }, (_, i) => (
          <line key={`v${i}`} x1={i * 50} x2={i * 50} y1="0" y2="160" />
        ))}
        {Array.from({ length: 5 }, (_, i) => (
          <line key={`h${i}`} x1="0" x2="500" y1={i * 40} y2={i * 40} />
        ))}
        {values.length > 1 && <polyline points={points} />}
        {values.length === 1 && <circle cx="20" cy="80" r="3" />}
        {!values.length && (
          <text x="250" y="85" textAnchor="middle">
            CONNECT A DEVICE TO OBSERVE
          </text>
        )}
      </svg>
      <footer>
        <span>RECEIVED READINGS · {values.length}/40</span>
        <span>
          {values.length
            ? `${min}–${max} ${device ? profiles[device.kind].unit : ''}`
            : 'AWAITING INPUT'}
        </span>
      </footer>
      <p>Recent received values, oldest to newest. Display only; no extra device reads.</p>
    </section>
  );
}
export default function TestBench({
  lab,
  device,
  selected,
  plan,
  run,
  activeRun,
  serverMode,
  serverReady,
  busy,
  canOperate,
  onSelect,
  onPlan,
  onConnect,
  onStart,
  onCancel,
  action,
  onExport,
  onResults,
}: {
  lab: LabState;
  device?: Device;
  selected: string;
  plan: string;
  run?: TestRun;
  activeRun?: TestRun;
  serverMode: boolean;
  serverReady: boolean;
  busy: boolean;
  canOperate: boolean;
  onSelect: (id: string) => void;
  onPlan: (id: string) => void;
  onConnect: () => void;
  onStart: () => void;
  onCancel: () => void;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
  onExport: (run: TestRun) => void;
  onResults: (run: TestRun) => void;
}) {
  const [emulationOpen, setEmulationOpen] = useState(false);
  const selectedPlan = lab.testPlans?.find((p) => p.id === plan && p.kind === device?.kind);
  const available = !serverMode || serverReady;
  const planReady = !!device && (!!selectedPlan || plan in planNames);
  const ready = !!device?.connected && planReady && available && canOperate && !busy && !activeRun;
  const shownRun = activeRun ?? run;
  const complete = shownRun?.steps.filter((s) => s.status !== 'pending').length ?? 0;
  const status = activeRun ? 'RUNNING' : ready ? 'READY TO TEST' : 'SETUP REQUIRED';
  const checks = [
    {
      label: 'Test engine',
      good: available,
      detail: serverMode
        ? serverReady
          ? 'Flask connected'
          : 'Waiting for Flask'
        : 'Local simulator',
    },
    {
      label: 'Device hookup',
      good: !!device?.connected,
      detail: device
        ? `${device.name} · ${device.connected ? 'connected' : 'disconnected'}`
        : 'Select or add a device',
    },
    {
      label: 'Test sequence',
      good: planReady,
      detail: selectedPlan
        ? `${selectedPlan.name} · v${selectedPlan.version}`
        : planNames[plan as keyof typeof planNames],
    },
    {
      label: 'Bench access',
      good: canOperate && !busy && !activeRun,
      detail: !canOperate
        ? 'Operator role required'
        : activeRun
          ? 'A test owns the bench'
          : busy
            ? 'Applying a change'
            : 'Available',
    },
  ];
  return (
    <section className="panel runner instrument-bench" aria-label="Test bench controls">
      <header className="bench-faceplate">
        <div>
          <span className="eyebrow">HARDWARE TESTER / VALIDATION INSTRUMENT</span>
          <h2>Connection & response bench</h2>
        </div>
        <span className={`bench-state ${activeRun ? 'running' : ready ? 'ready' : ''}`}>
          <i />
          {status}
        </span>
      </header>
      <div className="bench-instrument-body">
        <SignalMonitor device={device} />
        <div className="bench-selector-panel">
          <span className="eyebrow">01 / CONNECT THE DEVICE</span>
          <label>
            Target device
            <select
              aria-label="Target device"
              value={selected}
              disabled={!!activeRun}
              onChange={(e) => onSelect(e.target.value)}
            >
              {!lab.devices.length && <option value="">No devices available</option>}
              {lab.devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </label>
          <div className="bench-hookup">
            <span className={`bench-jack ${device?.connected ? 'connected' : ''}`} />
            <span>
              {device
                ? `${device.protocol} · ${device.adapter ?? 'simulation'}`
                : 'No device selected'}
              <small>{device?.endpoint ?? 'Add a device to begin'}</small>
            </span>
          </div>
          <button
            className="button secondary"
            disabled={
              !device || !!device.connected || !canOperate || !available || busy || !!activeRun
            }
            onClick={onConnect}
          >
            <FiLink />
            {device?.connected ? 'Input connected' : 'Connect input'}
          </button>
          <span className="eyebrow bench-sequence-label">02 / SELECT THE SEQUENCE</span>
          <label>
            Test plan
            <select
              aria-label="Test plan"
              value={plan}
              disabled={!!activeRun}
              onChange={(e) => onPlan(e.target.value)}
            >
              {Object.entries(planNames).map(([id, label]) => (
                <option key={id} value={id}>
                  {label}
                </option>
              ))}
              {serverMode &&
                lab.testPlans
                  ?.filter((p) => p.kind === device?.kind)
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} · v{p.version}
                    </option>
                  ))}
            </select>
          </label>
          <p className="bench-plan-summary">
            {selectedPlan
              ? `${selectedPlan.steps.length} saved steps · ${selectedPlan.description || 'Custom test sequence'}`
              : plan === 'control'
                ? 'Connection, telemetry, output response, and restoration.'
                : 'Connection, telemetry, and operating-range checks.'}
          </p>
          <details className="bench-sequence-preview">
            <summary>Inspect selected sequence</summary>
            {selectedPlan ? (
              <ol>
                {selectedPlan.steps.map((s, i) => (
                  <li key={i}>
                    <strong>{s.name}</strong>
                    <small>{stepSummary(s)}</small>
                  </li>
                ))}
              </ol>
            ) : (
              <p>
                {plan === 'control'
                  ? 'Checks the connection and reading, commands a profile-specific output, checks the response, then restores the original output.'
                  : 'Checks the connection, reads telemetry, and checks against the device profile or attached peripheral limits.'}
              </p>
            )}
            <NavLink to="/plans">Open plan library</NavLink>
          </details>
        </div>
      </div>
      <div className="bench-readiness" aria-label="Bench readiness">
        {checks.map((c) => (
          <div key={c.label} className={c.good ? 'is-ready' : ''}>
            <span>{c.good ? <FiCheck /> : <FiCpu />}</span>
            <div>
              <strong>{c.label}</strong>
              <small>{c.detail}</small>
            </div>
          </div>
        ))}
      </div>
      {device && (
        <details
          className="bench-emulation"
          onToggle={(e) => setEmulationOpen(e.currentTarget.open)}
        >
          <summary>
            Emulator setup ·{' '}
            {device.scenario
              ? `${device.scenario.name} · v${device.scenario.version}`
              : device.fault !== 'none'
                ? device.fault
                : 'Normal device response'}
          </summary>
          {emulationOpen && (
            <ScenarioControls
              key={device.id}
              device={device}
              lab={lab}
              enabled={canOperate && serverMode && serverReady && !busy && !activeRun}
              serverMode={serverMode}
              action={action}
            />
          )}
        </details>
      )}
      <div className="bench-run-deck">
        <div>
          <span className="eyebrow">03 / EXECUTE & OBSERVE</span>
          <strong>
            {activeRun
              ? `Testing ${activeRun.deviceName}`
              : ready
                ? 'Bench ready. Start your test.'
                : 'Complete the setup checks above.'}
          </strong>
          <p>
            {device?.scenario
              ? `Scenario starts at read ${(device.scenarioCursor ?? 0) + 1}. Restart its sequence for a repeatable starting point.`
              : device?.fault !== 'none' && device
                ? `Manual fault active: ${device.fault}. A failed test may be expected.`
                : 'Each check reports its own result. Output commands include restoration.'}
          </p>
          {(device?.safetyWarning || device?.lastError) && (
            <p className="danger">{device.safetyWarning || device.lastError}</p>
          )}
        </div>
        <button
          className={`button bench-run-button ${activeRun ? 'secondary' : 'primary'}`}
          disabled={!canOperate || busy || !available || (!activeRun && !ready)}
          onClick={activeRun ? onCancel : onStart}
        >
          {activeRun ? <FiSquare /> : <FiPlay />}
          {activeRun ? 'Stop test' : 'Run test'}
        </button>
      </div>
      {shownRun ? (
        <div className="steps bench-run-record">
          <div className="result-heading">
            <strong>
              {shownRun.plan}
              <span className="muted"> / {shownRun.deviceName}</span>
            </strong>
            <span className={`status status-${shownRun.status}`}>
              <i />
              {shownRun.status}
            </span>
          </div>
          <div className="bench-progress">
            <span>
              {complete} / {shownRun.steps.length} checks reported
            </span>
            <progress
              aria-label="Test progress"
              value={complete}
              max={shownRun.steps.length || 1}
            />
          </div>
          {shownRun.steps.map((s, i) => (
            <div className={`step step-${s.status}`} key={i}>
              <span className="step-icon">
                {s.status === 'passed' ? <FiCheck /> : s.status === 'failed' ? <FiX /> : i + 1}
              </span>
              <div>
                <strong>{s.name}</strong>
                <p>{s.detail}</p>
              </div>
              <span className="step-state">{s.status}</span>
            </div>
          ))}
          {shownRun.status !== 'running' && (
            <div className="bench-result-actions">
              <p>
                {shownRun.status === 'passed'
                  ? 'All required checks passed.'
                  : shownRun.status === 'cancelled'
                    ? 'Test stopped. Review the checks and restoration before retrying.'
                    : 'A check failed. Open the report for observations and expected values.'}
              </p>
              <button className="button secondary" onClick={() => onResults(shownRun)}>
                Inspect report
              </button>
              <button className="button secondary" onClick={() => onExport(shownRun)}>
                Export run
              </button>
              <button
                className="button secondary"
                disabled={!ready || shownRun.deviceId !== selected}
                onClick={onStart}
              >
                Run selected setup again
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bench-awaiting">
          <FiPlay />
          <strong>No test recorded yet</strong>
          <p>Connect an input and choose a sequence. Results will appear here as checks finish.</p>
        </div>
      )}
    </section>
  );
}
