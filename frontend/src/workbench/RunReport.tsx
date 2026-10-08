import { Device, LabState, profiles, TestRun } from './simulator';
import './reports.css';
export default function RunReport({
  run,
  lab,
  enabled,
  onRerun,
  onExport,
  onLogs,
}: {
  run: TestRun;
  lab: LabState;
  enabled: boolean;
  onRerun: (d: Device, p: string) => void;
  onExport: () => void;
  onLogs: () => void;
}) {
  const target = lab.devices.find((d) => d.id === run.deviceId);
  const id =
    run.configuration?.plan.id ??
    run.planId ??
    (run.plan === 'Control response'
      ? 'control'
      : run.plan === 'Connection & health'
        ? 'smoke'
        : '');
  const saved = lab.testPlans?.find((p) => p.id === id);
  const available = id === 'smoke' || id === 'control' || !!saved;
  const changed =
    !!run.configuration &&
    ((saved && saved.version !== run.configuration.plan.version) ||
      (!!target &&
        [
          'name',
          'kind',
          'protocol',
          'adapter',
          'endpoint',
          'baudrate',
          'fault',
          'scenarioCursor',
        ].some(
          (k) => target[k as keyof Device] !== run.configuration!.device[k as keyof Device],
        )) ||
      JSON.stringify(lab.peripherals?.filter((p) => p.device_id === run.deviceId) ?? []) !==
        JSON.stringify(run.configuration.peripherals) ||
      JSON.stringify(target?.scenario) !== JSON.stringify(run.configuration.device.scenario));
  const passed = run.steps.filter((s) => s.status === 'passed').length;
  const duration = run.finishedAt
    ? Math.max(0, new Date(run.finishedAt).getTime() - new Date(run.startedAt).getTime())
    : null;
  const unit = run.configuration ? profiles[run.configuration.device.kind].unit : '';
  return (
    <section className="panel run-report" aria-label="Run report">
      <header>
        <div>
          <span className="eyebrow">EXECUTION REPORT</span>
          <h2>{run.deviceName}</h2>
          <p>
            {run.plan} · {new Date(run.startedAt).toLocaleString()}
          </p>
        </div>
        <span className={`report-verdict ${run.status}`}>{run.status}</span>
      </header>
      {run.configuration?.device.scenario && (
        <p className="helper">
          Scenario: {run.configuration.device.scenario.name} · v
          {run.configuration.device.scenario.version} ·{' '}
          {run.configuration.device.scenarioCursor ?? 0} staged reads consumed before this run.
          Restart the sequence in the device inspector to repeat its initial conditions.
        </p>
      )}
      <div className="report-metrics">
        <div>
          <strong>
            {passed}/{run.steps.length}
          </strong>
          <span>Checks passed</span>
          <div
            className="report-progress"
            role="img"
            aria-label={`${passed} of ${run.steps.length} checks passed`}
          >
            <i style={{ width: `${run.steps.length ? (passed / run.steps.length) * 100 : 0}%` }} />
          </div>
        </div>
        <div>
          <strong>{duration === null ? '—' : `${(duration / 1000).toFixed(1)}s`}</strong>
          <span>Total elapsed time</span>
        </div>
        <div>
          <strong>
            {run.restoration === 'restored'
              ? 'Restored'
              : run.restoration === 'not-needed'
                ? 'Unchanged'
                : run.restoration === 'failed'
                  ? 'Needs attention'
                  : '—'}
          </strong>
          <span>Output restoration{!run.restoration ? ' not recorded' : ''}</span>
        </div>
      </div>
      <div className="report-actions">
        <button
          className="button primary"
          disabled={
            !enabled ||
            !target?.connected ||
            !available ||
            run.status === 'running' ||
            (!!saved && saved.kind !== target?.kind)
          }
          onClick={() => {
            if (
              target &&
              (!changed ||
                window.confirm(
                  'The device settings, scenario position, or plan version have changed. Rerun using the current configuration?',
                ))
            )
              onRerun(target, id);
          }}
        >
          Rerun test
        </button>
        <button className="button secondary" onClick={onExport}>
          Export this run
        </button>
        <button className="button secondary" onClick={onLogs}>
          View run logs
        </button>
      </div>
      <p className="helper">
        Rerun target: {target?.name ?? 'Device removed'} ·{' '}
        {saved ? `${saved.name} v${saved.version}` : available ? run.plan : 'Plan removed'}.{' '}
        {changed ? 'Configuration changed since this run. ' : ''}
        {!target?.connected ? 'Connect the target before rerunning. ' : ''}Reruns use current device
        settings and the current plan.
      </p>
      <h3>Measurements and checks</h3>
      <p className="helper">
        Each marker is a recorded step reading. The green band shows its expected range; readings
        are not a continuous telemetry trace. Timing bars compare recorded execution durations;
        simulated steps execute immediately.
      </p>
      <div className="report-checks">
        {run.steps.map((s, i) => {
          const e = s.expected;
          const low = e?.min ?? (e?.value !== undefined ? e.value - (e.tolerance ?? 0) : undefined);
          const high =
            e?.max ?? (e?.value !== undefined ? e.value + (e.tolerance ?? 0) : undefined);
          const values = [s.observed, low, high].filter(
            (v): v is number => v !== undefined && Number.isFinite(v),
          );
          const min = Math.min(0, ...values);
          const profileMax =
            run.configuration?.device.kind === 'temperature'
              ? 50
              : run.configuration?.device.kind === 'valve'
                ? 100
                : 1;
          const max = Math.max(profileMax, ...values);
          const span = max - min;
          const left = (v: number) => ((v - min) / span) * 100;
          const expected =
            e?.value !== undefined
              ? `${e.value}${unit} ± ${e.tolerance ?? 0}`
              : low !== undefined && high !== undefined
                ? `${low}–${high}${unit}`
                : 'Not recorded';
          return (
            <details
              className={`report-check ${s.status}`}
              key={i}
              open={
                s.status === 'failed' ||
                s.name === 'Validate operating range' ||
                s.name === 'Verify response'
              }
            >
              <summary>
                <b>{i + 1}</b>
                <strong>{s.name}</strong>
                <span>{s.status}</span>
              </summary>
              <div className="report-check-body">
                <div className="measurement-labels">
                  <span>
                    Expected <strong>{expected}</strong>
                  </span>
                  <span>
                    Actual{' '}
                    <strong>
                      {s.observed === undefined ? 'No reading' : `${s.observed}${unit}`}
                    </strong>
                  </span>
                </div>
                {s.observed !== undefined && (
                  <div
                    className="measurement-track"
                    role="img"
                    aria-label={`Actual ${s.observed}${unit}; expected ${expected}`}
                  >
                    <span className="measurement-axis" />
                    {low !== undefined && high !== undefined && (
                      <i
                        className="measurement-band"
                        style={{
                          left: `${left(low)}%`,
                          width: `${Math.max(1, left(high) - left(low))}%`,
                        }}
                      />
                    )}
                    <b className="measurement-marker" style={{ left: `${left(s.observed)}%` }} />
                  </div>
                )}
                {s.observed !== undefined && (
                  <div className="measurement-scale">
                    <span>
                      {min}
                      {unit}
                    </span>
                    <span>
                      {max}
                      {unit}
                    </span>
                  </div>
                )}
                <p>{s.detail}</p>
                <div
                  className="step-timing"
                  role="img"
                  aria-label={
                    s.durationMs === undefined
                      ? 'Step timing unavailable'
                      : `Step duration ${s.durationMs} milliseconds`
                  }
                >
                  <i
                    style={{
                      width: `${s.durationMs === undefined ? 0 : (s.durationMs / Math.max(1, ...run.steps.map((x) => x.durationMs ?? 0))) * 100}%`,
                    }}
                  />
                </div>
                <small>
                  {s.durationMs === undefined
                    ? 'Step timing not recorded'
                    : `${s.durationMs} ms executing step`}
                  {s.finishedAt ? ` · ${new Date(s.finishedAt).toLocaleTimeString()}` : ''}
                </small>
              </div>
            </details>
          );
        })}
      </div>
      {run.configuration && (
        <details className="report-config">
          <summary>
            Configuration captured for this run · plan v{run.configuration.plan.version}
          </summary>
          <pre className="run-configuration">{JSON.stringify(run.configuration, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}
