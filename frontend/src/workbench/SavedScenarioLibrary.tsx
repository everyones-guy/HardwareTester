import { useEffect, useState } from 'react';
import { FiChevronDown, FiChevronLeft, FiChevronRight, FiSearch } from 'react-icons/fi';
import type { Scenario, ScenarioFrame } from './ScenarioLibrary';
import { LabState } from './simulator';

export const scenarioBehaviors: Record<ScenarioFrame['behavior'], string> = {
  healthy: 'Healthy response',
  timeout: 'No response / timeout',
  'out-of-range': 'Out-of-range reading',
  delay: 'Delayed response',
};

export default function SavedScenarioLibrary({
  lab,
  enabled,
  revealId,
  revealVersion,
  onEdit,
  onExport,
  onDelete,
}: {
  lab: LabState;
  enabled: boolean;
  revealId: string;
  revealVersion: number;
  onEdit: (s: Scenario, copy?: boolean) => void;
  onExport: (s: Scenario) => void;
  onDelete: (s: Scenario) => void;
}) {
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('all');
  const [behavior, setBehavior] = useState('all');
  const [sort, setSort] = useState('presets');
  const [rows, setRows] = useState(5);
  const [page, setPage] = useState(0);
  const [open, setOpen] = useState('');
  const scenarios = lab.scenarios ?? [];
  const filtered = scenarios
    .filter(
      (s) =>
        (s.name + ' ' + s.description).toLowerCase().includes(query.toLowerCase()) &&
        (kind === 'all' || (kind === 'preset') === s.builtin) &&
        (behavior === 'all' || s.frames.some((f) => f.behavior === behavior)),
    )
    .sort((a, b) =>
      sort === 'stages'
        ? b.frames.length - a.frames.length || a.name.localeCompare(b.name)
        : sort === 'name'
          ? a.name.localeCompare(b.name)
          : Number(b.builtin) - Number(a.builtin) || a.name.localeCompare(b.name),
    );
  const last = Math.max(0, Math.ceil(filtered.length / rows) - 1);
  const current = Math.min(page, last);
  useEffect(() => {
    if (!revealId) return;
    setQuery('');
    setKind('all');
    setBehavior('all');
    setSort('presets');
    setOpen(revealId);
    const ordered = [...scenarios].sort(
      (a, b) => Number(b.builtin) - Number(a.builtin) || a.name.localeCompare(b.name),
    );
    setPage(Math.max(0, Math.floor(ordered.findIndex((s) => s.id === revealId) / rows)));
  }, [revealId, revealVersion]);
  function filter(change: () => void) {
    change();
    setPage(0);
    setOpen('');
  }
  return (
    <section className="panel scenario-library" aria-label="Saved scenario library">
      <header>
        <div>
          <span className="eyebrow">RESPONSE PATTERN CATALOG</span>
          <h2>Saved scenarios</h2>
          <p>Choose a pattern, inspect its stages, then apply it from a device.</p>
        </div>
        <span className="scenario-library-count">{scenarios.length} patterns</span>
      </header>
      <div className="scenario-library-toolbar">
        <label className="scenario-library-search">
          <FiSearch />
          <input
            aria-label="Search scenarios"
            placeholder="Find a name or description…"
            value={query}
            onChange={(e) => filter(() => setQuery(e.target.value))}
          />
        </label>
        <label>
          Response
          <select
            aria-label="Filter scenario behavior"
            value={behavior}
            onChange={(e) => filter(() => setBehavior(e.target.value))}
          >
            <option value="all">All responses</option>
            {Object.entries(scenarioBehaviors).map(([id, label]) => (
              <option key={id} value={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Sort
          <select
            aria-label="Sort scenarios"
            value={sort}
            onChange={(e) => filter(() => setSort(e.target.value))}
          >
            <option value="presets">Presets first</option>
            <option value="name">Name A–Z</option>
            <option value="stages">Most stages</option>
          </select>
        </label>
        <label>
          Cards
          <select
            aria-label="Visible scenario cards"
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
      <div className="scenario-library-tabs" role="group" aria-label="Filter scenario type">
        {['all', 'preset', 'custom'].map((k) => (
          <button key={k} aria-pressed={kind === k} onClick={() => filter(() => setKind(k))}>
            {k === 'all' ? 'All patterns' : k === 'preset' ? 'Presets' : 'Custom'}{' '}
            <span>
              {scenarios.filter((s) => k === 'all' || (k === 'preset') === s.builtin).length}
            </span>
          </button>
        ))}
      </div>
      <div className="scenario-pattern-legend">
        <span>
          <i className="healthy" />
          Healthy
        </span>
        <span>
          <i className="timeout" />
          Timeout
        </span>
        <span>
          <i className="out-of-range" />
          Bad reading
        </span>
        <span>
          <i className="delay" />
          Delayed
        </span>
      </div>
      <div className="scenario-library-tray">
        {filtered.slice(current * rows, (current + 1) * rows).map((s) => {
          const total = s.frames.reduce((n, f) => n + f.count, 0);
          const applied = lab.devices.filter((d) => d.scenario?.id === s.id);
          const expanded = open === s.id;
          return (
            <article
              className={`scenario-card scenario-library-card ${expanded ? 'expanded' : ''}`}
              key={s.id}
            >
              <button
                className="scenario-card-toggle"
                aria-label={`Scenario ${s.name}`}
                aria-expanded={expanded}
                onClick={() => setOpen(expanded ? '' : s.id)}
              >
                <span className={`scenario-library-icon ${s.builtin ? 'preset' : 'custom'}`}>
                  {s.builtin ? 'P' : 'C'}
                </span>
                <span className="scenario-card-name">
                  <strong>{s.name}</strong>
                  <small>
                    {s.builtin ? 'Preset' : 'Custom'} · v{s.version} · {s.frames.length}{' '}
                    {s.frames.length === 1 ? 'stage' : 'stages'} · {total}{' '}
                    {total === 1 ? 'read' : 'reads'}
                  </small>
                </span>
                {applied.length > 0 && (
                  <span className="scenario-in-use">{applied.length} in use</span>
                )}
                <FiChevronDown />
              </button>
              <div
                className="scenario-pattern-strip"
                role="img"
                aria-label={s.frames
                  .map(
                    (f) =>
                      `${f.count} ${scenarioBehaviors[f.behavior]}${f.behavior === 'delay' ? ` at ${f.delayMs} milliseconds` : ''}`,
                  )
                  .join(', ')}
              >
                {s.frames.map((f, i) => (
                  <i key={i} className={f.behavior} style={{ flexGrow: f.count }} />
                ))}
              </div>
              {expanded && (
                <div className="scenario-card-details">
                  <h3>{s.name}</h3>
                  <span className="scenario-tag">
                    {s.builtin ? 'PRESET' : 'CUSTOM'} · v{s.version}
                  </span>
                  <p>{s.description || 'No description provided.'}</p>
                  <ol className="scenario-sequence">
                    {s.frames.map((f, i) => (
                      <li key={i}>
                        <span className="scenario-stage-index">
                          {String(i + 1).padStart(2, '0')}
                        </span>
                        <b>{f.count}×</b> {scenarioBehaviors[f.behavior]}
                        {f.behavior === 'delay' ? ` · ${f.delayMs} ms` : ''}
                      </li>
                    ))}
                  </ol>
                  <p className="scenario-tail">
                    Final behavior repeats:{' '}
                    <strong>{scenarioBehaviors[s.frames[s.frames.length - 1].behavior]}</strong>
                  </p>
                  {applied.length > 0 && (
                    <p className="scenario-usage">
                      Applied to{' '}
                      {applied
                        .map((d) => `${d.name} (snapshot v${d.scenario!.version})`)
                        .join(', ')}
                      .
                    </p>
                  )}
                  <div className="scenario-buttons">
                    {!s.builtin && (
                      <button
                        className="button secondary"
                        disabled={!enabled}
                        onClick={() => onEdit(s)}
                      >
                        Edit
                      </button>
                    )}
                    <button
                      className="button secondary"
                      disabled={!enabled}
                      onClick={() => onEdit(s, true)}
                    >
                      Duplicate
                    </button>
                    <button className="button secondary" onClick={() => onExport(s)}>
                      Export
                    </button>
                    {!s.builtin && (
                      <button
                        className="text-button danger"
                        disabled={!enabled}
                        onClick={() => onDelete(s)}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              )}
            </article>
          );
        })}
        {!filtered.length && (
          <div className="scenario-library-empty">
            <FiSearch />
            <h3>{scenarios.length ? 'No scenarios match' : 'No saved scenarios yet'}</h3>
            <p>
              {scenarios.length
                ? 'Try a different search or response filter.'
                : 'Connect Flask to load the shared library.'}
            </p>
            {scenarios.length > 0 && (
              <button
                className="button secondary"
                onClick={() =>
                  filter(() => {
                    setQuery('');
                    setKind('all');
                    setBehavior('all');
                  })
                }
              >
                Clear scenario filters
              </button>
            )}
          </div>
        )}
      </div>
      <footer className="scenario-library-footer">
        <span>
          {filtered.length
            ? `${current * rows + 1}–${Math.min((current + 1) * rows, filtered.length)} of ${filtered.length} patterns`
            : '0 patterns'}
          <small>OPEN A CARD TO INSPECT ITS SEQUENCE</small>
        </span>
        <div>
          <button
            className="icon-button"
            aria-label="Previous scenario page"
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
            aria-label="Next scenario page"
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
