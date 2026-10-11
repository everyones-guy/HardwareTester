import { useState } from 'react';
import type { LabState, TestRun } from './simulator';
import { profiles } from './simulator';
import {
  configurationChanges,
  eligibleBaseline,
  elapsedMs,
  expectedRange,
  matchingStep,
  numeric,
  sameSeries,
} from './resultMetrics';
import './result-analysis.css';

const number = (value: number | undefined, unit = '') =>
  numeric(value) ? `${Number(value.toFixed(2))}${unit}` : 'Not recorded';
const delta = (a: number | undefined, b: number | undefined, unit = '') =>
  numeric(a) && numeric(b) ? `${a - b > 0 ? '+' : ''}${Number((a - b).toFixed(2))}${unit}` : '—';
const label = (run: TestRun) =>
  `${new Date(run.startedAt).toLocaleString()} · ${run.status} · ${run.id.slice(0, 8)}`;

export default function ResultAnalysis({
  run,
  lab,
  canMark,
  onBaseline,
  onInspect,
}: {
  run: TestRun;
  lab: LabState;
  canMark: boolean;
  onBaseline: (run: TestRun, enabled: boolean) => void;
  onInspect: (id: string) => void;
}) {
  const [referenceId, setReferenceId] = useState('');
  const [metric, setMetric] = useState('elapsed');
  const [includeChanged, setIncludeChanged] = useState(false);
  const [windowSize, setWindowSize] = useState(30);
  const series = lab.runs
    .filter((r) => r.status !== 'running' && sameSeries(r, run))
    .sort((a, b) => Date.parse(b.startedAt) - Date.parse(a.startedAt));
  const baseline = series.find((r) => r.baseline);
  const choices = series.filter((r) => r.id !== run.id);
  const reference =
    choices.find((r) => r.id === referenceId) ??
    choices.find((r) => r.id === baseline?.id) ??
    choices[0];
  const changes = reference ? configurationChanges(run, reference) : [];
  const unit = run.configuration ? profiles[run.configuration.device.kind].unit : '';
  const index = metric === 'elapsed' ? -1 : Number(metric);
  const range = index < 0 ? undefined : expectedRange(run.steps[index]);
  const metricUnit = index < 0 ? ' ms' : unit;
  const measure = (r: TestRun) =>
    index < 0 ? elapsedMs(r) : matchingStep(run, r, index) ? r.steps[index]?.observed : undefined;
  const comparable = series.filter((r) => r.id === run.id || !configurationChanges(run, r).length);
  const trend = (includeChanged ? series : comparable).slice(0, windowSize).reverse();
  const readings = trend.map(measure);
  const baselineChanged = baseline ? configurationChanges(run, baseline).length > 0 : false;
  const baselineValue = baseline && (includeChanged || !baselineChanged) ? measure(baseline) : undefined;
  const values = [...readings, ...(range ?? []), baselineValue].filter(
    numeric,
  );
  const low = values.length ? Math.min(...values) : 0;
  const high = values.length ? Math.max(...values) : 1;
  const padding = Math.max((high - low) * 0.12, Math.abs(high) * 0.02, 0.5);
  const min = low - padding,
    max = high + padding;
  const x = (i: number) => (trend.length <= 1 ? 420 : 65 + (i / (trend.length - 1)) * 710);
  const y = (v: number) => 190 - ((v - min) / (max - min)) * 160;
  const regressed = reference
    ? run.steps.filter(
        (s, i) =>
          matchingStep(run, reference, i) &&
          s.status === 'failed' &&
          reference.steps[i].status === 'passed',
      ).length
    : 0;
  const improved = reference
    ? run.steps.filter(
        (s, i) =>
          matchingStep(run, reference, i) &&
          s.status === 'passed' &&
          reference.steps[i].status === 'failed',
      ).length
    : 0;
  const expected = (r: TestRun, i: number) => {
    const e = expectedRange(r.steps[i]);
    const u = r.configuration ? profiles[r.configuration.device.kind].unit : '';
    return e ? `${number(e[0], u)} to ${number(e[1], u)}` : 'Not recorded';
  };
  return (
    <section className="panel result-analysis" aria-label="Result comparison and trends">
      <header className="panel-heading">
        <div>
          <span className="eyebrow">BENCH MEMORY</span>
          <h2>Compare & track</h2>
          <p>
            {run.deviceName} · {run.plan}. Comparing retained runs for this device and plan.
          </p>
        </div>
        <span className="analysis-count">{series.length} completed runs</span>
      </header>
      <div className="baseline-strip">
        <div>
          <span className="eyebrow">KNOWN-GOOD BASELINE</span>
          <strong>{baseline ? label(baseline) : 'No baseline selected'}</strong>
          <small>
            {run.baseline
              ? 'This is the saved reference run.'
              : 'Choose a completed passing run as your reference.'}
          </small>
        </div>
        <button
          className="button secondary"
          disabled={
            !canMark ||
            !lab.runs.some((r) => r.id === run.id) ||
            (!run.baseline && !eligibleBaseline(run))
          }
          onClick={() => onBaseline(run, !run.baseline)}
        >
          {run.baseline ? 'Clear baseline' : 'Use this run as baseline'}
        </button>
      </div>
      <p className="helper">
        One baseline per device and plan. Replacing it preserves the recorded checks. Baselines
        remain within the last 100 retained runs; export important reports for longer storage.
        Operators and admins can change them on an idle bench.
      </p>
      <details className="analysis-disclosure" open>
        <summary>
          Side-by-side comparison{' '}
          <span>
            {reference
              ? `${regressed} checks regressed · ${improved} improved`
              : 'Run this test again to compare'}
          </span>
        </summary>
        <div className="analysis-body">
          <label className="analysis-control">
            Reference run
            <select
              aria-label="Reference run"
              value={reference?.id ?? ''}
              disabled={!choices.length}
              onChange={(e) => setReferenceId(e.target.value)}
            >
              {!choices.length && <option value="">No other completed runs</option>}
              {choices.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.baseline ? 'BASELINE · ' : ''}
                  {label(r)}
                </option>
              ))}
            </select>
          </label>
          {reference ? (
            <>
              <div
                className={`comparison-context ${changes.length ? 'changed' : ''}`}
                role="status"
              >
                <strong>
                  {changes.length
                    ? 'Changed setup — review before drawing conclusions'
                    : 'Matching recorded configuration'}
                </strong>
                <p>
                  {changes.length
                    ? changes.join(' · ')
                    : 'Plan, transport, scenario starting position, and peripherals match.'}
                </p>
              </div>
              <div className="comparison-summary">
                <div>
                  <span>Verdict · reference → selected</span>
                  <strong>
                    {reference.status} → {run.status}
                  </strong>
                </div>
                <div>
                  <span>Elapsed difference · selected − reference</span>
                  <strong>{delta(elapsedMs(run), elapsedMs(reference), ' ms')}</strong>
                </div>
                <div>
                  <span>Output restoration · reference → selected</span>
                  <strong>
                    {reference.restoration ?? 'Not recorded'} → {run.restoration ?? 'Not recorded'}
                  </strong>
                </div>
              </div>
              <div className="comparison-scroll">
                <div className="comparison-table" role="table" aria-label="Check comparison">
                  <div role="row" className="comparison-row comparison-head">
                    {['Check', 'Reference run', 'Selected run', 'Reading difference'].map((s) => (
                      <strong role="columnheader" key={s}>
                        {s}
                      </strong>
                    ))}
                  </div>
                  {Array.from(
                    { length: Math.max(run.steps.length, reference.steps.length) },
                    (_, i) => {
                      const a = run.steps[i],
                        b = reference.steps[i],
                        aligned = matchingStep(run, reference, i);
                      return (
                        <div role="row" className="comparison-row" key={i}>
                          <strong role="rowheader">
                            {i + 1}. {a?.name ?? b?.name}
                            {!aligned && (
                              <small>Step or profile differs / metadata unavailable</small>
                            )}
                          </strong>
                          {[
                            { r: reference, s: b },
                            { r: run, s: a },
                          ].map(({ r, s }) => (
                            <div role="cell" key={r.id}>
                              <b className={`analysis-outcome ${s?.status ?? 'pending'}`}>
                                {s?.status ?? 'Step absent'}
                              </b>
                              <strong>
                                {number(
                                  s?.observed,
                                  r.configuration ? profiles[r.configuration.device.kind].unit : '',
                                )}
                              </strong>
                              <small>Expected: {expected(r, i)}</small>
                              <small>Step time: {number(s?.durationMs, ' ms')}</small>
                            </div>
                          ))}
                          <div role="cell">
                            <strong>{aligned ? delta(a?.observed, b?.observed, unit) : '—'}</strong>
                            <small>
                              {aligned ? 'Selected − reference' : 'Check definitions differ'}
                            </small>
                          </div>
                        </div>
                      );
                    },
                  )}
                </div>
              </div>
              <p className="helper">
                A changed reading or duration alone does not mean a regression. Regressed checks
                passed in the reference and failed in the selected run. Recorded expectations appear
                beside both readings.
              </p>
            </>
          ) : (
            <p className="empty">
              No second run for this device and plan yet. Rerun the test below to build a
              comparison.
            </p>
          )}
        </div>
      </details>
      <details className="analysis-disclosure" open>
        <summary>
          History trend <span>{readings.filter(numeric).length} recorded points</span>
        </summary>
        <div className="analysis-body">
          <div className="trend-controls">
            <label className="analysis-control">
              Metric
              <select
                aria-label="Trend metric"
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
              >
                <option value="elapsed">Total elapsed time</option>
                {run.steps.map((s, i) => (
                  <option key={i} value={i}>
                    {i + 1}. {s.name} · reading
                  </option>
                ))}
              </select>
            </label>
            <label className="analysis-control">
              Window
              <select
                aria-label="Trend window"
                value={windowSize}
                onChange={(e) => setWindowSize(Number(e.target.value))}
              >
                {[10, 30, 100].map((n) => (
                  <option key={n} value={n}>
                    Latest {n} runs
                  </option>
                ))}
              </select>
            </label>
            <label className="trend-toggle">
              <input
                type="checkbox"
                checked={includeChanged}
                onChange={(e) => setIncludeChanged(e.target.checked)}
              />
              Include changed configurations
            </label>
          </div>
          <p className="helper">
            {includeChanged
              ? 'Changed setups are included. Review each report’s configuration.'
              : `${series.length - comparable.length} runs with changed or missing configuration excluded.`}{' '}
            Oldest → newest, equally spaced by run order. Measurements are discrete test readings.
            Missing values leave gaps.
            {' '}Values in {index < 0 ? 'milliseconds' : unit || 'profile units (unit not recorded for older reports)'}.{baselineChanged && !includeChanged ? ' Baseline line omitted because its configuration differs.' : ''}
          </p>
          {values.length && readings.some(numeric) ? (
            <>
              <svg
                className="trend-chart"
                viewBox="0 0 840 230"
                role="img"
                aria-label={`History trend: ${readings.filter(numeric).length} readings, ${metric === 'elapsed' ? 'milliseconds' : run.steps[index]?.name}. Oldest to newest.`}
              >
                <title>Recorded values over repeated runs</title>
                {[0, 1, 2, 3, 4].map((n) => (
                  <g key={n}>
                    <line
                      className="trend-grid"
                      x1="65"
                      x2="775"
                      y1={30 + n * 40}
                      y2={30 + n * 40}
                    />
                    <text x="60" y={34 + n * 40} textAnchor="end">
                      {number(max - (n / 4) * (max - min))}
                    </text>
                  </g>
                ))}
                {range && (
                  <rect
                    className="trend-band"
                    x="65"
                    y={y(range[1])}
                    width="710"
                    height={Math.max(2, y(range[0]) - y(range[1]))}
                  />
                )}
                {numeric(baselineValue) && (
                  <line
                    className="trend-baseline"
                    x1="65"
                    x2="775"
                    y1={y(baselineValue)}
                    y2={y(baselineValue)}
                  />
                )}
                {readings.map((v, i) =>
                  numeric(v) ? (
                    <g key={trend[i].id}>
                      {i > 0 && numeric(readings[i - 1]) && (
                        <line
                          className="trend-signal"
                          x1={x(i - 1)}
                          x2={x(i)}
                          y1={y(readings[i - 1]!)}
                          y2={y(v)}
                        />
                      )}
                      <circle
                        className={`trend-point ${trend[i].status}`}
                        cx={x(i)}
                        cy={y(v)}
                        r={trend[i].id === run.id ? 7 : 5}
                        onClick={() => onInspect(trend[i].id)}
                      >
                        <title>
                          {label(trend[i])}: {number(v, metricUnit)}
                        </title>
                      </circle>
                    </g>
                  ) : null,
                )}
                <text x="65" y="218">
                  Oldest
                </text>
                <text x="775" y="218" textAnchor="end">
                  Newest
                </text>
              </svg>
              <p className="trend-legend">
                Dots show run verdicts; exact labels appear below{' '}
                {range
                  ? `· Shaded expected range: ${number(range[0], unit)} to ${number(range[1], unit)} (selected run)`
                  : '· No expected band recorded for this metric'}
                {numeric(baselineValue)
                  ? ` · Dashed baseline: ${number(baselineValue, metricUnit)}`
                  : ''}
              </p>
            </>
          ) : (
            <p className="empty">No recorded values for this metric in the selected window.</p>
          )}
          <details className="trend-records">
            <summary>View plotted runs and exact values ({trend.length})</summary>
            <div>
              {trend.map((r, i) => (
                <button className="trend-record" key={r.id} onClick={() => onInspect(r.id)}>
                  <span>
                    {label(r)}
                    {r.baseline ? ' · BASELINE' : ''}
                    {r.id === run.id ? ' · SELECTED' : ''}
                  </span>
                  <strong>{number(readings[i], metricUnit)}</strong>
                </button>
              ))}
            </div>
          </details>
        </div>
      </details>
    </section>
  );
}

