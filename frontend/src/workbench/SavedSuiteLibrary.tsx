import { useEffect, useState } from 'react';
import { FiChevronDown, FiChevronLeft, FiChevronRight, FiLayers, FiSearch } from 'react-icons/fi';
import { ValidationSuite } from './backend';
import { LabState, planNames, profiles } from './simulator';
import './suite-catalog.css';
export const expectedLabel = (outcomes: string[]) =>
  outcomes.map((s) => (s === 'passed' ? 'Pass' : 'Fail')).join(' → ');
const attempts = (s: ValidationSuite) => s.cases.reduce((n, c) => n + c.expected.length, 0);
export default function SavedSuiteLibrary({
  lab,
  enabled,
  canAdmin,
  revealId,
  revealVersion,
  onSelect,
  onEdit,
  onDelete,
}: {
  lab: LabState;
  enabled: boolean;
  canAdmin: boolean;
  revealId: string;
  revealVersion: number;
  onSelect: (s: ValidationSuite) => void;
  onEdit: (s: ValidationSuite, copy?: boolean) => void;
  onDelete: (s: ValidationSuite) => void;
}) {
  const suites = lab.validationSuites ?? [];
  const [query, setQuery] = useState('');
  const [profile, setProfile] = useState('all');
  const [outcome, setOutcome] = useState('all');
  const [sort, setSort] = useState('name');
  const [rows, setRows] = useState(5);
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState('');
  const [catalogOpen, setCatalogOpen] = useState(true);
  const byName = (a: ValidationSuite, b: ValidationSuite) =>
    a.name.localeCompare(b.name) || a.id.localeCompare(b.id);
  const filtered = suites
    .filter(
      (s) =>
        `${s.name} ${s.description} ${s.cases.map((c) => c.name).join(' ')}`
          .toLowerCase()
          .includes(query.trim().toLowerCase()) &&
        (profile === 'all' || s.kind === profile) &&
        (outcome === 'all' ||
          s.cases.some((c) =>
            outcome === 'recovery'
              ? c.expected.some(
                  (v, i) => v === 'failed' && c.expected.slice(i + 1).includes('passed'),
                )
              : c.expected.includes(outcome as 'passed' | 'failed'),
          )),
    )
    .sort(
      (a, b) =>
        (sort === 'cases'
          ? b.cases.length - a.cases.length
          : sort === 'attempts'
            ? attempts(b) - attempts(a)
            : 0) || byName(a, b),
    );
  const last = Math.max(0, Math.ceil(filtered.length / rows) - 1);
  const current = Math.min(page, last);
  useEffect(() => {
    if (!revealId) return;
    setCatalogOpen(true);
    setQuery('');
    setProfile('all');
    setOutcome('all');
    setSort('name');
    setOpen(revealId);
    setPage(
      Math.max(0, Math.floor([...suites].sort(byName).findIndex((s) => s.id === revealId) / rows)),
    );
  }, [revealId, revealVersion]);
  function filter(change: () => void) {
    change();
    setPage(0);
    setOpen('');
  }
  function exportSuite(s: ValidationSuite) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(s, null, 2)], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'validation-suite.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <section className="panel suite-catalog" aria-label="Saved validation suites">
      <header>
        <div>
          <span className="eyebrow">EXPECTED OUTCOME CATALOG</span>
          <h2>Saved suites</h2>
          <p>
            Inspect the cases and expectations, then select a suite for the validation sequencer.
          </p>
        </div>
        <button
          className="text-button"
          aria-expanded={catalogOpen}
          onClick={() => setCatalogOpen(!catalogOpen)}
        >
          {catalogOpen ? 'Collapse saved suites' : 'Expand saved suites'}
          <FiChevronDown />
        </button>
      </header>
      {!catalogOpen && (
        <p className="suite-editor-summary">
          {suites.length} saved suites · Expand to browse cases and expectations.
        </p>
      )}
      {catalogOpen && (
        <>
          <div className="suite-catalog-toolbar">
            <label className="suite-catalog-search">
              <FiSearch />
              <input
                aria-label="Search suites"
                value={query}
                placeholder="Find a suite or case…"
                onChange={(e) => filter(() => setQuery(e.target.value))}
              />
            </label>
            <label>
              Expects
              <select
                aria-label="Filter suite expectations"
                value={outcome}
                onChange={(e) => filter(() => setOutcome(e.target.value))}
              >
                <option value="all">All outcomes</option>
                <option value="passed">Includes a pass</option>
                <option value="failed">Includes a failure</option>
                <option value="recovery">Failure then recovery</option>
              </select>
            </label>
            <label>
              Sort
              <select
                aria-label="Sort suites"
                value={sort}
                onChange={(e) => filter(() => setSort(e.target.value))}
              >
                <option value="name">Name A–Z</option>
                <option value="cases">Most cases</option>
                <option value="attempts">Most attempts</option>
              </select>
            </label>
            <label>
              Cards
              <select
                aria-label="Visible suite cards"
                value={rows}
                onChange={(e) => filter(() => setRows(Number(e.target.value)))}
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n} at a time
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="suite-catalog-tabs" role="group" aria-label="Filter suite profile">
            {['all', ...Object.keys(profiles)].map((k) => (
              <button
                key={k}
                aria-pressed={profile === k}
                onClick={() => filter(() => setProfile(k))}
              >
                {k === 'all' ? 'All profiles' : profiles[k as ValidationSuite['kind']].name}
                <span>{suites.filter((s) => k === 'all' || s.kind === k).length}</span>
              </button>
            ))}
          </div>
          <div className="suite-lineup-legend">
            <span>
              <i className="passed" />
              Expect pass
            </span>
            <span>
              <i className="failed" />
              Expect failure
            </span>
          </div>
          <div className="suite-catalog-tray">
            {filtered.slice(current * rows, (current + 1) * rows).map((s) => {
              const expanded = open === s.id;
              const plan = lab.testPlans?.find((p) => p.id === s.planId && p.kind === s.kind);
              const missing =
                (!(s.planId in planNames) && !plan) ||
                s.cases.some((c) => !lab.scenarios?.some((v) => v.id === c.scenarioId));
              return (
                <article
                  className={`catalog-item suite-catalog-card ${expanded ? 'expanded' : ''}`}
                  key={s.id}
                >
                  <button
                    className="suite-card-toggle"
                    aria-label={`Validation suite ${s.name}`}
                    aria-expanded={expanded}
                    onClick={() => setOpen(expanded ? '' : s.id)}
                  >
                    <span className="suite-catalog-icon">
                      <FiLayers />
                    </span>
                    <span className="suite-card-name">
                      <strong>{s.name}</strong>
                      <small>
                        {profiles[s.kind].name} · v{s.version} · {s.cases.length}{' '}
                        {s.cases.length === 1 ? 'case' : 'cases'} · {attempts(s)} attempts
                        {missing ? ' · Setup needed' : ''}
                      </small>
                    </span>
                    <FiChevronDown />
                  </button>
                  <div
                    className="suite-lineup-strip"
                    role="img"
                    aria-label={s.cases
                      .map((c) => `${c.name}: expect ${expectedLabel(c.expected)}`)
                      .join(', ')}
                  >
                    {s.cases.flatMap((c, i) =>
                      c.expected.map((v, n) => <i key={`${i}-${n}`} className={v} />),
                    )}
                  </div>
                  {expanded && (
                    <div className="suite-card-details">
                      <h3>{s.name}</h3>
                      <p>{s.description || 'No description provided.'}</p>
                      <p className="suite-catalog-plan">
                        Plan:{' '}
                        {plan?.name ??
                          planNames[s.planId as keyof typeof planNames] ??
                          'Missing plan'}{' '}
                        · Uses current saved versions when run
                      </p>
                      {missing && (
                        <p className="suite-dependency-warning">
                          A plan or scenario is missing. Edit the suite and choose a replacement
                          before running.
                        </p>
                      )}
                      <ol className="suite-case-index">
                        {s.cases.map((c, i) => (
                          <li key={i}>
                            <span>{String(i + 1).padStart(2, '0')}</span>
                            <div>
                              <strong>{c.name}</strong>
                              <small>
                                {lab.scenarios?.find((v) => v.id === c.scenarioId)?.name ??
                                  'Missing scenario'}
                              </small>
                            </div>
                            <b>{expectedLabel(c.expected)}</b>
                          </li>
                        ))}
                      </ol>
                      <div className="suite-card-actions">
                        <button
                          className="button primary"
                          disabled={!enabled || missing}
                          onClick={() => onSelect(s)}
                        >
                          Select for run
                        </button>
                        <button
                          className="button secondary"
                          disabled={!enabled || !canAdmin}
                          onClick={() => onEdit(s)}
                        >
                          Edit
                        </button>
                        <button
                          className="button secondary"
                          disabled={!enabled || !canAdmin}
                          onClick={() => onEdit(s, true)}
                        >
                          Duplicate
                        </button>
                        <button className="button secondary" onClick={() => exportSuite(s)}>
                          Export JSON
                        </button>
                        <button
                          className="text-button danger"
                          disabled={!enabled || !canAdmin}
                          onClick={() => onDelete(s)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
            {!filtered.length && (
              <div className="suite-catalog-empty">
                <FiSearch />
                <h3>{suites.length ? 'No suites match' : 'No saved suites yet'}</h3>
                <p>
                  {suites.length
                    ? 'Try another search, profile, or expectation.'
                    : 'Save the starter suite to validate healthy, bad-reading, and recovery responses.'}
                </p>
                {suites.length > 0 && (
                  <button
                    className="button secondary"
                    onClick={() =>
                      filter(() => {
                        setQuery('');
                        setProfile('all');
                        setOutcome('all');
                      })
                    }
                  >
                    Clear suite filters
                  </button>
                )}
              </div>
            )}
          </div>
          <footer className="suite-catalog-footer">
            <span>
              {filtered.length
                ? `${current * rows + 1}–${Math.min((current + 1) * rows, filtered.length)} of ${filtered.length} suites`
                : '0 suites'}
              <small>OPEN A CARD TO INSPECT ITS EXPECTATIONS</small>
            </span>
            <div>
              <button
                className="icon-button"
                aria-label="Previous suite page"
                disabled={current === 0}
                onClick={() => {
                  setPage(current - 1);
                  setOpen('');
                }}
              >
                <FiChevronLeft />
              </button>
              <span>
                {current + 1} / {last + 1}
              </span>
              <button
                className="icon-button"
                aria-label="Next suite page"
                disabled={current >= last}
                onClick={() => {
                  setPage(current + 1);
                  setOpen('');
                }}
              >
                <FiChevronRight />
              </button>
            </div>
          </footer>
        </>
      )}
    </section>
  );
}
