import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { FiCheck, FiChevronRight, FiPlay } from 'react-icons/fi';
import { Device, LabState, TestRun, planNames, profiles } from './simulator';
import { ScenarioControls } from './ScenarioLibrary';
import { ServerResponse } from './backend';
import './guided-test.css';

export interface ReadinessCheck {
  label: string;
  good: boolean;
  detail?: string;
}

export default function GuidedTest({
  lab,
  device,
  plan,
  ready,
  checks,
  editable,
  canStop,
  connectable,
  serverMode,
  onSelect,
  onPlan,
  onConnect,
  onStart,
  onCancel,
  action,
  onResults,
}: {
  lab: LabState;
  device?: Device;
  plan: string;
  ready: boolean;
  checks: ReadinessCheck[];
  editable: boolean;
  canStop: boolean;
  connectable: boolean;
  serverMode: boolean;
  onSelect: (id: string) => void;
  onPlan: (id: string) => void;
  onConnect: () => void;
  onStart: () => Promise<string | undefined>;
  onCancel: () => void;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
  onResults: (run: TestRun) => void;
}) {
  const [step, setStep] = useState(0);
  const [runId, setRunId] = useState('');
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState('');
  const run = lab.runs.find((r) => r.id === runId);
  const capturedDevice = run?.configuration?.device;
  const unit = capturedDevice
    ? profiles[capturedDevice.kind].unit
    : run?.deviceId === device?.id && device
      ? profiles[device.kind].unit
      : '';
  const saved = serverMode
    ? lab.testPlans?.find((p) => p.id === plan && p.kind === device?.kind)
    : undefined;
  const planReady = !!device && (!!saved || plan in planNames);
  const writes = saved ? saved.steps.some((s) => s.action === 'set') : plan === 'control';
  const simulated = !device?.adapter || device.adapter === 'simulation';
  const stages = ['Choose input', 'Choose test', 'Check & run', 'Read result'];
  async function launch() {
    setError('');
    setLaunching(true);
    try {
      const id = await onStart();
      if (id) {
        setRunId(id);
        setStep(3);
      } else
        setError(
          'The test did not start. Review the bench checks and workspace message, then retry.',
        );
    } catch {
      setError('The test could not start. Check the connection and retry.');
    } finally {
      setLaunching(false);
    }
  }
  return (
    <section className="guided-test" aria-label="Guided test setup">
      <header>
        <div>
          <span className="eyebrow">BENCH ASSISTANT</span>
          <h3>Your next successful test</h3>
        </div>
        <span>{String(step + 1).padStart(2, '0')} / 04</span>
      </header>
      <nav aria-label="Guided test steps">
        {stages.map((label, i) => (
          <button
            key={label}
            aria-current={step === i ? 'step' : undefined}
            disabled={
              launching ||
              !!lab.runs.find((r) => r.status === 'running') ||
              (i === 1 && !device) ||
              (i === 2 && !planReady) ||
              (i === 3 && !runId)
            }
            onClick={() => setStep(i)}
          >
            <b>{i + 1}</b>
            {label}
          </button>
        ))}
      </nav>
      <div className="guided-test-body">
        {step === 0 && (
          <>
            <h4>What are we testing?</h4>
            <p>Start with a simulated input, or choose a configured serial or MQTT device.</p>
            <label>
              Input
              <select
                aria-label="Guided input"
                value={device?.id ?? ''}
                disabled={!editable}
                onChange={(e) => {
                  onSelect(e.target.value);
                  onPlan('smoke');
                }}
              >
                <option value="" disabled>
                  Choose an input…
                </option>
                {lab.devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} · {d.adapter ?? 'simulation'}
                  </option>
                ))}
              </select>
            </label>
            {device && (
              <div className="guided-hookup">
                <strong>
                  {profiles[device.kind].name} ·{' '}
                  {simulated ? 'Simulated input' : `${device.adapter?.toUpperCase()} hardware`}
                </strong>
                <code>{device.endpoint}</code>
                <p>
                  {simulated
                    ? 'Use this input to learn the workflow without wiring a device.'
                    : 'The device must answer the Hardware Tester JSON read/set protocol with a matching request ID and a numeric value.'}
                </p>
                {!simulated && (
                  <p>
                    {device.adapter === 'serial'
                      ? 'The serial port belongs to the machine running Flask. Check the port and baud rate; a USB mouse does not speak this protocol.'
                      : 'The MQTT device must subscribe to its base topic /command and reply on /reply. A Raspberry Pi can host the responder.'}
                  </p>
                )}
              </div>
            )}
            {!lab.devices.length && (
              <p>
                No inputs configured yet. Add one in <NavLink to="/devices">Devices</NavLink>.
              </p>
            )}
            {device?.lastError && (
              <p role="alert" className="danger">
                {device.lastError}
              </p>
            )}
            <div className="guided-actions">
              <NavLink to="/devices">Configure devices</NavLink>
              <button
                className="button secondary"
                disabled={!connectable || !!device?.connected}
                onClick={onConnect}
              >
                {device?.connected ? 'Input connected' : 'Connect guided input'}
              </button>
              <button
                className="button primary"
                disabled={!device?.connected || !editable}
                onClick={() => setStep(1)}
              >
                Choose test <FiChevronRight />
              </button>
            </div>
          </>
        )}
        {step === 1 && (
          <>
            <h4>What should the device do?</h4>
            <p>
              Connection & health is a useful first test. Choose output testing once you are ready
              to command the device.
            </p>
            <label>
              Compatible test plan
              <select
                aria-label="Guided sequence"
                value={plan}
                disabled={!editable}
                onChange={(e) => onPlan(e.target.value)}
              >
                {!planReady && <option value={plan}>Choose an available plan</option>}
                {Object.entries(planNames).map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
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
            <p className="guided-command-note">
              {writes
                ? 'Commands output: this plan changes device output and attempts to restore the original value afterward.'
                : 'Read-only test: this plan observes the input without setting device output.'}
            </p>
            {device && simulated && (
              <details>
                <summary>Optional simulation scenario</summary>
                <ScenarioControls
                  key={device.id}
                  device={device}
                  lab={lab}
                  enabled={editable && serverMode}
                  serverMode={serverMode}
                  action={action}
                />
              </details>
            )}
            <p>
              {device?.scenario
                ? `Applied scenario: ${device.scenario.name}. Next read: ${(device.scenarioCursor ?? 0) + 1}. Restart it above for a repeatable starting point.`
                : device?.fault && device.fault !== 'none'
                  ? `Manual fault active: ${device.fault}. A failed check may be expected.`
                  : 'Normal device response selected.'}
            </p>
            <div className="guided-actions">
              <button className="button secondary" onClick={() => setStep(0)}>
                Back to input
              </button>
              <button
                className="button primary"
                disabled={!planReady || !editable}
                onClick={() => setStep(2)}
              >
                Review readiness <FiChevronRight />
              </button>
            </div>
          </>
        )}
        {step === 2 && (
          <>
            <h4>{ready ? 'Ready for the first reading' : 'A few things need attention'}</h4>
            <p>
              {device?.name ?? 'No input'} ·{' '}
              {saved?.name ?? planNames[plan as keyof typeof planNames] ?? 'Missing plan'}
            </p>
            <ul className="guided-checks">
              {checks.map((c) => (
                <li key={c.label} className={c.good ? 'good' : ''}>
                  <span>{c.good ? <FiCheck /> : '!'}</span>
                  <div>
                    <strong>{c.label}</strong>
                    <small>{c.detail}</small>
                  </div>
                </li>
              ))}
            </ul>
            {writes && (
              <p className="guided-command-note">
                This test commands output. Check the wiring and load before running; review
                restoration in the report afterward.
              </p>
            )}
            {device?.safetyWarning && (
              <p role="alert" className="danger">
                {device.safetyWarning}
              </p>
            )}
            {error && (
              <p role="alert" className="danger">
                {error}
              </p>
            )}
            <div className="guided-actions">
              <button className="button secondary" disabled={launching} onClick={() => setStep(1)}>
                Back to test
              </button>
              <button
                className="button primary"
                disabled={!ready || launching}
                onClick={() => void launch()}
              >
                <FiPlay />
                {launching ? 'Starting test…' : 'Start guided test'}
              </button>
            </div>
          </>
        )}
        {step === 3 && (
          <div aria-live="polite">
            <h4>
              {!run
                ? 'Waiting for the test record…'
                : run.status === 'running'
                  ? 'Taking measurements…'
                  : run.status === 'passed'
                    ? 'Your test passed'
                    : run.status === 'cancelled'
                      ? 'Your test was stopped'
                      : 'Your test found a problem'}
            </h4>
            {run && (
              <>
                <p>
                  {run.deviceName} · {run.plan} ·{' '}
                  {run.steps.filter((s) => s.status === 'passed').length}/{run.steps.length} checks
                  passed
                </p>
                {capturedDevice?.scenario && (
                  <p>
                    Simulation scenario for this run: {capturedDevice.scenario.name}. A detected
                    fault can be intentional; use a validation suite to check expected failures
                    automatically.
                  </p>
                )}
                <div className="guided-measurements">
                  {run.steps.map((s, i) => (
                    <article key={i} className={`guided-measurement ${s.status}`}>
                      <span>{s.status}</span>
                      <strong>{s.name}</strong>
                      {s.observed !== undefined && (
                        <b>
                          {s.observed} <em>{unit}</em>
                        </b>
                      )}
                      <p>
                        {s.expected
                          ? `Expected: ${s.expected.value !== undefined ? `${s.expected.value}${s.expected.tolerance !== undefined ? ` ± ${s.expected.tolerance}` : ''}` : `${s.expected.min ?? '−∞'} to ${s.expected.max ?? '∞'}`}`
                          : 'See check details below.'}
                      </p>
                      <small>{s.detail}</small>
                    </article>
                  ))}
                </div>
                <p>
                  {run.restoration
                    ? `Output restoration: ${run.restoration}.`
                    : 'The report retains the test setup and individual check details.'}
                </p>
                <div className="guided-actions">
                  {run.status === 'running' ? (
                    <button className="button secondary" disabled={!canStop} onClick={onCancel}>
                      Stop guided test
                    </button>
                  ) : (
                    <>
                      <button className="button secondary" onClick={() => onResults(run)}>
                        Open guided report
                      </button>
                      <button
                        className="button primary"
                        disabled={!editable}
                        onClick={() => {
                          onSelect(run.deviceId);
                          onPlan(run.planId ?? 'smoke');
                          setStep(2);
                        }}
                      >
                        Review & rerun
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
