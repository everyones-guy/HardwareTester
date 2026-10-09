import { useEffect, useState } from 'react';
import { FiChevronDown, FiChevronLeft, FiChevronRight, FiSearch } from 'react-icons/fi';
import { NavLink } from 'react-router-dom';
import { SavedPlan } from './backend';
import { SavedSteps, stepActions } from './PlanStepRow';

const profiles = { temperature: 'Temperature sensor', valve: 'Valve', relay: 'Relay' };
export default function SavedPlanLibrary({
  plans,
  enabled,
  revealId,
  revealVersion,
  onEdit,
  onExport,
  onDelete,
}: {
  plans: SavedPlan[];
  enabled: boolean;
  revealId: string;
  revealVersion: number;
  onEdit: (plan: SavedPlan, copy?: boolean) => void;
  onExport: (plan: SavedPlan) => void;
  onDelete: (plan: SavedPlan) => void;
}) {
  const [query, setQuery] = useState('');
  const [profile, setProfile] = useState('all');
  const [action, setAction] = useState('all');
  const [sort, setSort] = useState('name');
  const [rows, setRows] = useState(5);
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState('');
  const filtered = plans
    .filter(
      (p) =>
        `${p.name} ${p.description}`.toLowerCase().includes(query.trim().toLowerCase()) &&
        (profile === 'all' || p.kind === profile) &&
        (action === 'all' || p.steps.some((s) => s.action === action)),
    )
    .sort(
      (a, b) =>
        (sort === 'steps'
          ? b.steps.length - a.steps.length
          : sort === 'version'
            ? b.version - a.version
            : 0) ||
        a.name.localeCompare(b.name) ||
        a.id.localeCompare(b.id),
    );
  const last = Math.max(0, Math.ceil(filtered.length / rows) - 1);
  const current = Math.min(page, last);
  useEffect(() => {
    if (!revealId) return;
    setQuery('');
    setProfile('all');
    setAction('all');
    setSort('name');
    setOpen(revealId);
    const ordered = [...plans].sort(
      (a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id),
    );
    setPage(Math.max(0, Math.floor(ordered.findIndex((p) => p.id === revealId) / rows)));
  }, [revealId, revealVersion]);
  function filter(change: () => void) {
    change();
    setPage(0);
    setOpen('');
  }
  return (
    <section className="panel plan-catalog" aria-label="Saved test plan library">
      <header>
        <div>
          <span className="eyebrow">TEST SEQUENCE CATALOG</span>
          <h2>Saved test plans</h2>
          <p>
            Inspect a sequence, then choose a matching device on the{' '}
            <NavLink to="/tests">test bench</NavLink>. Every result captures its plan version.
          </p>
        </div>
        <span className="plan-catalog-count">{plans.length} plans</span>
      </header>
      <div className="plan-catalog-toolbar">
        <label className="plan-catalog-search">
          <FiSearch />
          <input
            aria-label="Search test plans"
            placeholder="Find a name or description…"
            value={query}
            onChange={(e) => filter(() => setQuery(e.target.value))}
          />
        </label>
        <label>
          Contains
          <select
            aria-label="Filter plan action"
            value={action}
            onChange={(e) => filter(() => setAction(e.target.value))}
          >
            <option value="all">All actions</option>
            {Object.entries(stepActions).map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Sort
          <select
            aria-label="Sort test plans"
            value={sort}
            onChange={(e) => filter(() => setSort(e.target.value))}
          >
            <option value="name">Name A–Z</option>
            <option value="steps">Most steps</option>
            <option value="version">Highest version</option>
          </select>
        </label>
        <label>
          Cards
          <select
            aria-label="Visible test plan cards"
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
      <div className="plan-catalog-tabs" role="group" aria-label="Filter plan profile">
        {['all', ...Object.keys(profiles)].map((k) => (
          <button key={k} aria-pressed={profile === k} onClick={() => filter(() => setProfile(k))}>
            {k === 'all' ? 'All profiles' : profiles[k as SavedPlan['kind']]}{' '}
            <span>{plans.filter((p) => k === 'all' || p.kind === k).length}</span>
          </button>
        ))}
      </div>
      <div className="plan-sequence-legend">
        {Object.entries(stepActions).map(([id, label]) => (
          <span key={id}>
            <i className={id} />
            {label}
          </span>
        ))}
      </div>
      <div className="plan-catalog-tray">
        {filtered.slice(current * rows, (current + 1) * rows).map((p) => {
          const expanded = open === p.id;
          const waits = p.steps.reduce(
            (n, s) => n + (s.action === 'wait' ? (s.seconds ?? 1) : 0),
            0,
          );
          return (
            <article
              className={`catalog-item plan-catalog-card ${expanded ? 'expanded' : ''}`}
              key={p.id}
            >
              <button
                className="plan-card-toggle"
                aria-label={`Test plan ${p.name}`}
                aria-expanded={expanded}
                onClick={() => setOpen(expanded ? '' : p.id)}
              >
                <span className={`plan-catalog-icon ${p.kind}`}>
                  {p.kind === 'temperature' ? '°C' : p.kind === 'valve' ? '%' : 'I/O'}
                </span>
                <span className="plan-card-name">
                  <strong>{p.name}</strong>
                  <small>
                    {profiles[p.kind]} · version {p.version} · {p.steps.length}{' '}
                    {p.steps.length === 1 ? 'step' : 'steps'}
                  </small>
                </span>
                <FiChevronDown />
              </button>
              <div
                className="plan-sequence-strip"
                role="img"
                aria-label={p.steps
                  .map((s, i) => `Step ${i + 1}: ${stepActions[s.action]}`)
                  .join(', ')}
              >
                {p.steps.map((s, i) => (
                  <i key={i} className={s.action} />
                ))}
              </div>
              {expanded && (
                <div className="plan-card-details">
                  <h3>{p.name}</h3>
                  <p>{p.description || 'No description provided.'}</p>
                  <p className="plan-sequence-note">
                    {p.steps.filter((s) => s.action.startsWith('assert_')).length} checks · {waits}s
                    configured waits
                    {p.steps.some((s) => s.action === 'set')
                      ? ' · Original output restored after every run'
                      : ''}
                  </p>
                  <SavedSteps steps={p.steps} />
                  <div className="plan-card-actions">
                    <button
                      className="button secondary"
                      disabled={!enabled}
                      onClick={() => onEdit(p)}
                    >
                      Edit
                    </button>
                    <button
                      className="button secondary"
                      disabled={!enabled}
                      onClick={() => onEdit(p, true)}
                    >
                      Duplicate
                    </button>
                    <button className="button secondary" onClick={() => onExport(p)}>
                      Export JSON
                    </button>
                    <button
                      className="text-button danger"
                      disabled={!enabled}
                      onClick={() => onDelete(p)}
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
          <div className="plan-catalog-empty">
            <FiSearch />
            <h3>{plans.length ? 'No test plans match' : 'No saved test plans yet'}</h3>
            <p>
              {plans.length
                ? 'Try another search, profile, or action.'
                : 'Save your first plan to start testing.'}
            </p>
            {plans.length > 0 && (
              <button
                className="button secondary"
                onClick={() =>
                  filter(() => {
                    setQuery('');
                    setProfile('all');
                    setAction('all');
                  })
                }
              >
                Clear plan filters
              </button>
            )}
          </div>
        )}
      </div>
      <footer className="plan-catalog-footer">
        <span>
          {filtered.length
            ? `${current * rows + 1}–${Math.min((current + 1) * rows, filtered.length)} of ${filtered.length} plans`
            : '0 plans'}
          <small>OPEN A CARD TO INSPECT ITS SEQUENCE</small>
        </span>
        <div>
          <button
            className="icon-button"
            aria-label="Previous test plan page"
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
            aria-label="Next test plan page"
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
    </section>
  );
}
