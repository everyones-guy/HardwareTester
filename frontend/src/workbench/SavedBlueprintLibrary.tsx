import { useEffect, useState } from 'react';

import { FiChevronDown, FiChevronLeft, FiChevronRight, FiCpu, FiSearch } from 'react-icons/fi';

import { Blueprint } from './backend';

import './blueprint-library.css';

const profiles = { temperature: 'Temperature', valve: 'Valve', relay: 'Relay' };

export function BlueprintPreview({
  blueprint,
  showNotes = false,
}: {
  blueprint: Blueprint;
  showNotes?: boolean;
}) {
  return (
    <div className="blueprint-preview">
      <div
        className="blueprint-device-list"
        role="region"
        tabIndex={0}
        aria-label="Blueprint devices"
      >
        {blueprint.devices.map((d, i) => (
          <div key={i}>
            <span className={`blueprint-device-icon ${d.kind}`}>
              {String(i + 1).padStart(2, '0')}
            </span>

            <span>
              <strong>{d.name}</strong>

              <small>{profiles[d.kind as keyof typeof profiles] ?? d.kind}</small>
            </span>
          </div>
        ))}
      </div>

      <p className="blueprint-apply-note">
        Adds {blueprint.devices.length} disconnected simulated{' '}
        {blueprint.devices.length === 1 ? 'device' : 'devices'}. Existing bench devices stay in
        place.
      </p>

      {blueprint.warnings.length > 0 && (
        <details className="blueprint-notes" open={showNotes}>
          <summary>Import notes · {blueprint.warnings.length}</summary>

          <ul>
            {blueprint.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export default function SavedBlueprintLibrary({
  blueprints,

  enabled,

  revealId,

  revealVersion,

  onApply,

  onExport,

  onDelete,
}: {
  blueprints: Blueprint[];

  enabled: boolean;

  revealId: string;

  revealVersion: number;

  onApply: (b: Blueprint) => void;

  onExport: (b: Blueprint) => void;

  onDelete: (b: Blueprint) => void;
}) {
  const [query, setQuery] = useState('');

  const [profile, setProfile] = useState('all');

  const [sort, setSort] = useState('name');

  const [rows, setRows] = useState(5);

  const [page, setPage] = useState(0);

  const [open, setOpen] = useState('');

  const byName = (a: Blueprint, b: Blueprint) =>
    a.name.localeCompare(b.name) || a.id.localeCompare(b.id);

  const filtered = blueprints

    .filter(
      (b) =>
        `${b.name} ${b.description} ${b.devices.map((d) => d.name).join(' ')}`

          .toLowerCase()

          .includes(query.trim().toLowerCase()) &&
        (profile === 'all' || b.devices.some((d) => d.kind === profile)),
    )

    .sort((a, b) => (sort === 'devices' ? b.devices.length - a.devices.length : 0) || byName(a, b));

  const last = Math.max(0, Math.ceil(filtered.length / rows) - 1);

  const current = Math.min(page, last);

  useEffect(() => {
    if (!revealId) return;

    setQuery('');

    setProfile('all');

    setSort('name');

    setOpen(revealId);

    setPage(
      Math.max(
        0,

        Math.floor([...blueprints].sort(byName).findIndex((b) => b.id === revealId) / rows),
      ),
    );
  }, [revealId, revealVersion]);

  function filter(change: () => void) {
    change();

    setPage(0);

    setOpen('');
  }

  return (
    <section className="panel blueprint-catalog" aria-label="Saved blueprint library">
      <header>
        <div>
          <span className="eyebrow">BENCH CONFIGURATION CATALOG</span>

          <h2>Saved blueprints</h2>

          <p>
            Inspect the device lineup and import notes before adding a configuration to your bench.
          </p>
        </div>

        <span className="blueprint-catalog-count">{blueprints.length} blueprints</span>
      </header>

      <div className="blueprint-catalog-toolbar">
        <label className="blueprint-catalog-search">
          <FiSearch />

          <input
            aria-label="Search blueprints"

            placeholder="Find a blueprint or device…"

            value={query}

            onChange={(e) => filter(() => setQuery(e.target.value))}
          />
        </label>

        <label>
          Sort
          <select
            aria-label="Sort blueprints"

            value={sort}

            onChange={(e) => filter(() => setSort(e.target.value))}
          >
            <option value="name">Name A–Z</option>

            <option value="devices">Most devices</option>
          </select>
        </label>

        <label>
          Cards
          <select
            aria-label="Visible blueprint cards"

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

      <div className="blueprint-catalog-tabs" role="group" aria-label="Filter blueprint profile">
        {['all', ...Object.keys(profiles)].map((k) => (
          <button key={k} aria-pressed={profile === k} onClick={() => filter(() => setProfile(k))}>
            {k === 'all' ? 'All profiles' : profiles[k as keyof typeof profiles]}{' '}
            <span>
              {blueprints.filter((b) => k === 'all' || b.devices.some((d) => d.kind === k)).length}
            </span>
          </button>
        ))}
      </div>

      <div className="blueprint-lineup-legend">
        {Object.entries(profiles).map(([id, label]) => (
          <span key={id}>
            <i className={id} />

            {label}
          </span>
        ))}
      </div>

      <div className="blueprint-catalog-tray">
        {filtered.slice(current * rows, (current + 1) * rows).map((b) => {
          const expanded = open === b.id;

          return (
            <article
              className={`catalog-item blueprint-catalog-card ${expanded ? 'expanded' : ''}`}

              key={b.id}
            >
              <button
                className="blueprint-card-toggle"

                aria-label={`Blueprint ${b.name}`}

                aria-expanded={expanded}

                onClick={() => setOpen(expanded ? '' : b.id)}
              >
                <span className="blueprint-catalog-icon">
                  <FiCpu />
                </span>

                <span className="blueprint-card-name">
                  <strong>{b.name}</strong>

                  <small>
                    {b.devices.length} simulated {b.devices.length === 1 ? 'device' : 'devices'} ·{' '}
                    {Object.entries(profiles)

                      .filter(([kind]) => b.devices.some((d) => d.kind === kind))

                      .map(([, label]) => label)

                      .join(' / ')}
                  </small>
                </span>

                <FiChevronDown />
              </button>

              <div
                className="blueprint-lineup-strip"

                role="img"

                aria-label={b.devices

                  .map((d) => `${d.name}: ${profiles[d.kind as keyof typeof profiles] ?? d.kind}`)

                  .join(', ')}
              >
                {b.devices.map((d, i) => (
                  <i key={i} className={d.kind} />
                ))}
              </div>

              {expanded && (
                <div className="blueprint-card-details">
                  <h3>{b.name}</h3>

                  <p>{b.description || 'No description provided.'}</p>

                  <BlueprintPreview blueprint={b} />

                  <div className="blueprint-card-actions">
                    <button
                      className="button primary"

                      disabled={!enabled}

                      onClick={() => onApply(b)}
                    >
                      Add to bench
                    </button>

                    <button className="button secondary" onClick={() => onExport(b)}>
                      Export JSON
                    </button>

                    <button
                      className="text-button danger"

                      disabled={!enabled}

                      onClick={() => onDelete(b)}
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
          <div className="blueprint-catalog-empty">
            <FiSearch />

            <h3>{blueprints.length ? 'No blueprints match' : 'No saved blueprints yet'}</h3>

            <p>
              {blueprints.length
                ? 'Try another search or device profile.'
                : 'Import a configuration or capture your current bench.'}
            </p>

            {blueprints.length > 0 && (
              <button
                className="button secondary"

                onClick={() =>
                  filter(() => {
                    setQuery('');

                    setProfile('all');
                  })
                }
              >
                Clear blueprint filters
              </button>
            )}
          </div>
        )}
      </div>

      <footer className="blueprint-catalog-footer">
        <span>
          {filtered.length
            ? `${current * rows + 1}–${Math.min((current + 1) * rows, filtered.length)} of ${filtered.length} blueprints`
            : '0 blueprints'}

          <small>OPEN A CARD TO INSPECT ITS DEVICES</small>
        </span>

        <div>
          <button
            className="icon-button"

            aria-label="Previous blueprint page"

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

            aria-label="Next blueprint page"

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
