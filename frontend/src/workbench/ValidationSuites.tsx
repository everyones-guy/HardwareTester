import SavedSuiteLibrary, { expectedLabel } from './SavedSuiteLibrary';
import { useEffect, useRef, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { FiCheck, FiChevronDown, FiPlus, FiPlay, FiSquare, FiX } from 'react-icons/fi';
import { LabState, planNames, profiles, TestRun } from './simulator';
import { ServerResponse, ValidationSuite, SuiteCase, SuiteRun } from './backend';
import './validation-suites.css';

const starter = (): SuiteCase[] => [
  { name: 'Healthy baseline', scenarioId: 'preset-healthy', expected: ['passed'] },
  {
    name: 'Reject bad telemetry',
    scenarioId: 'preset-sustained-bad-reading',
    expected: ['failed'],
  },
  {
    name: 'Detect timeout, then recover',
    scenarioId: 'preset-recovery',
    expected: ['failed', 'passed'],
  },
];
export default function ValidationSuites({
  lab,
  enabled,
  canAdmin,
  serverMode,
  action,
  onReport,
}: {
  lab: LabState;
  enabled: boolean;
  canAdmin: boolean;
  serverMode: boolean;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
  onReport: (run: TestRun) => void;
}) {
  const [name, setName] = useState('Connection validation');
  const [description, setDescription] = useState('');
  const [kind, setKind] = useState<ValidationSuite['kind']>('temperature');
  const [plan, setPlan] = useState('smoke');
  const [cases, setCases] = useState<SuiteCase[]>(starter);
  const [editing, setEditing] = useState<ValidationSuite>();
  const [selected, setSelected] = useState('');
  const [target, setTarget] = useState('');
  const [view, setView] = useState('');
  const [revealId, setRevealId] = useState('');
  const [revealVersion, setRevealVersion] = useState(0);
  const [editorOpen, setEditorOpen] = useState(true);
  const [expanded, setExpanded] = useState<Set<number>>(new Set([0]));
  const [editorFocus, setEditorFocus] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (editorFocus) heading.current?.focus();
  }, [editorFocus]);
  function toggleCase(i: number) {
    setExpanded((old) => {
      const next = new Set(old);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }

  const suites = lab.validationSuites ?? [];
  const chosen = suites.find((s) => s.id === selected);
  const active = lab.suiteRuns?.find((r) => r.status === 'running');
  const report = active ?? lab.suiteRuns?.find((r) => r.id === view) ?? lab.suiteRuns?.[0];
  const idle = enabled && !active && !lab.runs.some((r) => r.status === 'running');
  const devices = lab.devices.filter((d) => d.kind === chosen?.kind && d.adapter === 'simulation');
  const total = cases.reduce((n, c) => n + c.expected.length, 0);
  const planAvailable =
    plan in planNames || lab.testPlans?.some((p) => p.id === plan && p.kind === kind);
  const valid =
    !!name.trim() &&
    planAvailable &&
    cases.length > 0 &&
    total <= 20 &&
    cases.every((c) => c.name.trim() && lab.scenarios?.some((s) => s.id === c.scenarioId));
  function reset() {
    setEditing(undefined);
    setName('Connection validation');
    setDescription('');
    setKind('temperature');
    setPlan('smoke');
    setCases(starter());
    setExpanded(new Set([0]));
    setEditorOpen(true);
  }
  function edit(s: ValidationSuite, duplicate = false) {
    setExpanded(new Set());
    setEditorOpen(true);
    setEditorFocus((n) => n + 1);
    setEditing(duplicate ? undefined : s);
    setName(duplicate ? `${s.name.slice(0, 90)} copy` : s.name);
    setDescription(s.description);
    setKind(s.kind);
    setPlan(s.planId);
    setCases(s.cases.map((c) => ({ ...c, expected: [...c.expected] })));
  }
  function exportReport(r: SuiteRun) {
    const url = URL.createObjectURL(
      new Blob(
        [
          JSON.stringify(
            {
              format: 'hardware-tester-validation-suite',
              version: 1,
              exportedAt: new Date().toISOString(),
              report: r,
            },
            null,
            2,
          ),
        ],
        { type: 'application/json' },
      ),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'validation-suite-report.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">PROVE THE TESTER</span>
          <h1>Validation suites</h1>
          <p>Run repeatable simulation cases and check that your test detects what it should.</p>
        </div>
      </div>
      {!serverMode && (
        <p className="backend-warning">
          Suites run on Flask and keep their progress when you leave this page.{' '}
          <NavLink to="/settings">Connect the shared workspace</NavLink>.
        </p>
      )}
      <section className="panel suite-console" aria-label="Suite runner">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">VALIDATION SEQUENCER</span>
            <h2>{active ? `Running ${active.suite.name}` : 'Run a saved suite'}</h2>
          </div>
          <span className={`status status-${active ? 'running' : 'pending'}`}>
            {active ? 'running' : 'simulation only'}
          </span>
        </div>
        <div className="suite-run-controls">
          <label>
            Validation suite
            <select
              aria-label="Validation suite"
              value={selected}
              disabled={!idle}
              onChange={(e) => {
                setSelected(e.target.value);
                setTarget('');
              }}
            >
              <option value="">Choose a saved suite…</option>
              {suites.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} · v{s.version}
                </option>
              ))}
            </select>
          </label>
          <label>
            Simulated device
            <select
              aria-label="Suite target device"
              value={target}
              disabled={!idle || !chosen}
              onChange={(e) => setTarget(e.target.value)}
            >
              <option value="">Choose a matching device…</option>
              {devices.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                  {d.connected ? '' : ' · disconnected'}
                </option>
              ))}
            </select>
          </label>
          <button
            className={`button ${active ? 'secondary' : 'primary'}`}
            disabled={
              active
                ? !enabled
                : !idle || !chosen || !devices.some((d) => d.id === target && d.connected)
            }
            onClick={async () => {
              const r = await action(
                active ? '/suite-runs/cancel' : `/validation-suites/${selected}/run`,
                'POST',
                active ? {} : { deviceId: target },
              );
              if (r?.suiteRunId) setView(r.suiteRunId);
            }}
          >
            {active ? <FiSquare /> : <FiPlay />}
            {active ? 'Stop suite' : 'Run suite'}
          </button>
        </div>
        <p className="suite-help">
          Connect a matching simulated device on the bench first. Each case restarts its scenario;
          repeated attempts within a case continue the sequence. Original simulation settings are
          restored when the suite ends.
        </p>
      </section>
      {report && (
        <section className="panel suite-report" aria-label="Validation suite report">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">EXPECTED / ACTUAL</span>
              <h2>
                {report.suite.name} · v{report.suite.version}
              </h2>
              <p>
                {report.device.name} · {report.plan.name} · {report.status}
              </p>
            </div>
            <button
              className="button secondary"
              disabled={report.status === 'running'}
              onClick={() => exportReport(report)}
            >
              Export suite report
            </button>
          </div>
          <p className="suite-help">
            {report.status === 'passed'
              ? 'Every test outcome matched its expectation.'
              : report.status === 'failed'
                ? 'One or more test outcomes differed from expectations.'
                : report.detail ||
                  'Cases run in order. A detected expected failure counts as a matched outcome.'}
          </p>
          {report.cases.map((c, i) => (
            <article className="suite-result-case" key={i}>
              <header>
                <span>{String(i + 1).padStart(2, '0')}</span>
                <div>
                  <strong>{c.name}</strong>
                  <small>
                    {c.scenario.name} · v{c.scenario.version}
                  </small>
                </div>
                <span className={`status status-${c.status}`}>{c.status}</span>
              </header>
              {c.expected.map((expected, n) => {
                const a = c.attempts[n];
                return (
                  <div
                    className={`suite-attempt ${a ? (a.matched ? 'matched' : 'mismatch') : ''}`}
                    key={n}
                  >
                    <span>{a ? a.matched ? <FiCheck /> : <FiX /> : n + 1}</span>
                    <div>
                      <strong>
                        {a
                          ? a.matched
                            ? expected === 'failed'
                              ? 'Expected failure detected'
                              : 'Expected pass confirmed'
                            : 'Unexpected outcome'
                          : 'Waiting for test'}
                      </strong>
                      <small>
                        Attempt {n + 1} · expected {expected} · actual{' '}
                        {a?.run.status ??
                          (c.runId && n === c.attempts.length ? 'running' : 'pending')}
                      </small>
                    </div>
                    {a && (
                      <button className="text-button" onClick={() => onReport(a.run)}>
                        Inspect test report
                      </button>
                    )}
                  </div>
                );
              })}
            </article>
          ))}
          {report.restoration && (
            <p className="suite-help">Original simulation settings: {report.restoration}.</p>
          )}
        </section>
      )}
      <div className="suite-management-grid">
        <section className="panel settings-panel" aria-label="Suite editor">
          <span className="eyebrow">DEFINE EXPECTATIONS</span>
          <div className="suite-editor-heading">
            <h2 ref={heading} tabIndex={-1}>
              {editing ? 'Edit validation suite' : 'New validation suite'}
            </h2>
            <button
              className="text-button"
              aria-expanded={editorOpen}
              onClick={() => setEditorOpen(!editorOpen)}
            >
              {editorOpen ? 'Collapse suite editor' : 'Expand suite editor'}
              <FiChevronDown />
            </button>
          </div>
          {!editorOpen && (
            <p className="suite-editor-summary">
              {name} · {cases.length} cases · {total} attempts
            </p>
          )}
          {editorOpen && (
            <>
              <label>
                Suite name
                <input
                  aria-label="Suite name"
                  maxLength={100}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
              <label>
                Description
                <input
                  aria-label="Suite description"
                  maxLength={2000}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </label>
              <label>
                Device profile
                <select
                  aria-label="Suite device profile"
                  value={kind}
                  onChange={(e) => {
                    setKind(e.target.value as typeof kind);
                    setPlan('smoke');
                  }}
                >
                  {Object.entries(profiles).map(([id, p]) => (
                    <option key={id} value={id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Test plan
                <select
                  aria-label="Suite test plan"
                  value={plan}
                  onChange={(e) => setPlan(e.target.value)}
                >
                  {!planAvailable && (
                    <option value={plan}>Missing plan — choose a replacement</option>
                  )}
                  {Object.entries(planNames).map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                  {lab.testPlans
                    ?.filter((p) => p.kind === kind)
                    .map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} · v{p.version}
                      </option>
                    ))}
                </select>
              </label>
              {!planAvailable && (
                <p role="alert" className="suite-editor-error">
                  Choose an available test plan.
                </p>
              )}
              <p className="suite-help">
                {cases.length}/10 cases · {total}/20 attempts. “Fail” matches any failed test
                outcome; inspect its report to confirm the reason. Saved suites use current plan and
                scenario versions when launched.
              </p>
              <div className="suite-editor-index-controls">
                <span>
                  {cases.length} CASES · {total} ATTEMPTS
                </span>
                <button
                  className="text-button"
                  onClick={() => setExpanded(new Set(cases.map((_, i) => i)))}
                >
                  Expand all cases
                </button>
                <button className="text-button" onClick={() => setExpanded(new Set())}>
                  Collapse all cases
                </button>
              </div>
              {total > 20 && (
                <p role="alert" className="suite-editor-error">
                  A suite supports at most 20 attempts.
                </p>
              )}
              {cases.map((c, i) => (
                <article className={`suite-case-row ${expanded.has(i) ? 'expanded' : ''}`} key={i}>
                  <button
                    className="suite-case-toggle"
                    aria-label={`Edit case ${i + 1}: ${c.name || 'Unnamed case'}`}
                    aria-expanded={expanded.has(i)}
                    onClick={() => toggleCase(i)}
                  >
                    <span>{String(i + 1).padStart(2, '0')}</span>
                    <div>
                      <strong>{c.name || 'Unnamed case'}</strong>
                      <small>
                        {lab.scenarios?.find((s) => s.id === c.scenarioId)?.name ??
                          'Missing scenario'}
                      </small>
                    </div>
                    <b>{expectedLabel(c.expected)}</b>
                    <FiChevronDown />
                  </button>
                  {(!c.name.trim() || !lab.scenarios?.some((s) => s.id === c.scenarioId)) && (
                    <p role="alert" className="suite-editor-error">
                      {!c.name.trim() ? 'Give this case a name.' : 'Choose an available scenario.'}
                    </p>
                  )}
                  {expanded.has(i) && (
                    <fieldset className="suite-case-editor">
                      <legend>Case {i + 1}</legend>
                      <label>
                        Case name
                        <input
                          aria-label={`Case ${i + 1} name`}
                          value={c.name}
                          maxLength={100}
                          onChange={(e) =>
                            setCases((old) =>
                              old.map((v, n) => (n === i ? { ...v, name: e.target.value } : v)),
                            )
                          }
                        />
                      </label>
                      <label>
                        Scenario
                        <select
                          aria-label={`Case ${i + 1} scenario`}
                          value={c.scenarioId}
                          onChange={(e) =>
                            setCases((old) =>
                              old.map((v, n) =>
                                n === i ? { ...v, scenarioId: e.target.value } : v,
                              ),
                            )
                          }
                        >
                          {!lab.scenarios?.some((s) => s.id === c.scenarioId) && (
                            <option value={c.scenarioId}>
                              Missing scenario — choose a replacement
                            </option>
                          )}
                          {lab.scenarios?.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} · v{s.version}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Expected outcomes
                        <select
                          aria-label={`Case ${i + 1} expected outcomes`}
                          value={c.expected.join(',')}
                          onChange={(e) =>
                            setCases((old) =>
                              old.map((v, n) =>
                                n === i
                                  ? {
                                      ...v,
                                      expected: e.target.value.split(',') as SuiteCase['expected'],
                                    }
                                  : v,
                              ),
                            )
                          }
                        >
                          {[
                            'passed',
                            'failed',
                            'failed,passed',
                            'failed,failed,passed',
                            'passed,passed',
                            'passed,failed',
                            'passed,failed,passed',
                            'passed,passed,passed',
                            'failed,failed',
                            'failed,failed,failed',
                            'failed,passed,passed',
                            'failed,passed,failed',
                            'passed,passed,failed',
                            'passed,failed,failed',
                          ].map((v) => (
                            <option key={v} value={v}>
                              {v
                                .split(',')
                                .map((x) => (x === 'passed' ? 'Pass' : 'Fail'))
                                .join(' → ')}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="inline">
                        <button
                          className="text-button"
                          disabled={i === 0}
                          onClick={() => {
                            setCases((old) => {
                              const next = [...old];
                              [next[i - 1], next[i]] = [next[i], next[i - 1]];
                              return next;
                            });
                            setExpanded(
                              (old) =>
                                new Set(
                                  [...old].map((n) => (n === i ? i - 1 : n === i - 1 ? i : n)),
                                ),
                            );
                          }}
                        >
                          Move case {i + 1} up
                        </button>
                        <button
                          className="text-button danger"
                          disabled={cases.length === 1}
                          onClick={() => {
                            setCases((old) => old.filter((_, n) => n !== i));
                            setExpanded(
                              (old) =>
                                new Set(
                                  [...old].filter((n) => n !== i).map((n) => (n > i ? n - 1 : n)),
                                ),
                            );
                          }}
                        >
                          Remove case {i + 1}
                        </button>
                      </div>
                    </fieldset>
                  )}
                </article>
              ))}
              <div className="suite-actions">
                <button
                  className="button secondary"
                  disabled={cases.length >= 10}
                  onClick={() => {
                    setExpanded((old) => new Set([...old, cases.length]));
                    setCases((old) => [
                      ...old,
                      {
                        name: 'New validation case',
                        scenarioId: 'preset-healthy',
                        expected: ['passed'],
                      },
                    ]);
                  }}
                >
                  <FiPlus />
                  Add case
                </button>
                <button
                  className="button primary"
                  disabled={!idle || !canAdmin || !valid}
                  onClick={async () => {
                    const r = await action(
                      editing ? `/validation-suites/${editing.id}` : '/validation-suites',
                      editing ? 'PUT' : 'POST',
                      { name, description, kind, planId: plan, cases, version: editing?.version },
                    );
                    if (r) {
                      setSelected(r.suiteId ?? editing?.id ?? '');
                      setRevealId(r.suiteId ?? editing?.id ?? '');
                      setRevealVersion((n) => n + 1);
                      reset();
                    }
                  }}
                >
                  {editing ? 'Save suite changes' : 'Save validation suite'}
                </button>
                <button className="button secondary" onClick={reset}>
                  New suite
                </button>
              </div>
            </>
          )}
        </section>
        <div className="suite-library-column">
          <SavedSuiteLibrary
            lab={lab}
            enabled={idle}
            canAdmin={canAdmin}
            revealId={revealId}
            revealVersion={revealVersion}
            onSelect={(s) => {
              setSelected(s.id);
              setTarget('');
            }}
            onEdit={edit}
            onDelete={(s) => {
              if (confirm(`Delete suite ${s.name}? Saved reports keep their snapshots.`))
                void action(`/validation-suites/${s.id}`, 'DELETE', { version: s.version });
            }}
          />
          <section
            className="panel settings-panel suite-history-panel"
            aria-label="Recent suite runs"
          >
            <h2>Recent suite runs</h2>
            {lab.suiteRuns?.map((r) => (
              <button className="suite-history" key={r.id} onClick={() => setView(r.id)}>
                <strong>{r.suite.name}</strong>
                <span>
                  {r.device.name} · {r.status} · {new Date(r.startedAt).toLocaleString()}
                </span>
              </button>
            ))}
            {!lab.suiteRuns?.length && (
              <p className="empty">Completed validation reports will appear here.</p>
            )}
          </section>
        </div>
      </div>
    </>
  );
}
