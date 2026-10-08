import { useState } from 'react';
import { LabState, LogEntry } from './simulator';
import './reports.css';
export default function EventLog({
  lab,
  full,
  selectedRun,
  onExport,
}: {
  lab: LabState;
  full: boolean;
  selectedRun: string;
  onExport: (logs: LogEntry[]) => void;
}) {
  const [query, setQuery] = useState('');
  const [level, setLevel] = useState('all');
  const [device, setDevice] = useState('all');
  const [run, setRun] = useState(full && selectedRun ? 'selected' : 'all');
  const [sort, setSort] = useState('newest');
  const [after, setAfter] = useState('');
  const [before, setBefore] = useState('');
  const filtered = lab.logs
    .filter(
      (l) =>
        (level === 'all' || l.level === level) &&
        l.message.toLowerCase().includes(query.toLowerCase()) &&
        (device === 'all' || l.deviceId === device) &&
        (run === 'all' || l.runId === (run === 'selected' ? selectedRun : run)) &&
        (!after || new Date(l.time) >= new Date(after)) &&
        (!before || new Date(l.time) <= new Date(before)),
    )
    .sort((a, b) =>
      sort === 'oldest'
        ? a.time.localeCompare(b.time)
        : sort === 'severity'
          ? { error: 0, info: 1, success: 2 }[a.level] -
              { error: 0, info: 1, success: 2 }[b.level] || b.time.localeCompare(a.time)
          : b.time.localeCompare(a.time),
    );
  const devices = Array.from(
    new Set([
      ...lab.devices.map((d) => d.id),
      ...lab.logs.map((l) => l.deviceId).filter((id): id is string => !!id),
    ]),
  );
  return (
    <section className="panel event-log">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">EVENT STREAM</span>
          <h2>Activity log</h2>
        </div>
        <button
          className="button secondary"
          aria-label="Export logs"
          onClick={() => onExport(filtered)}
        >
          Export filtered logs
        </button>
      </div>
      <div className="event-toolbar">
        <label>
          Search
          <input
            aria-label="Search logs"
            placeholder="Find an event…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <label>
          Severity
          <select aria-label="Filter logs" value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="all">All events</option>
            <option value="error">Errors</option>
            <option value="success">Successes</option>
            <option value="info">Info</option>
          </select>
        </label>
        <label>
          Sort
          <select aria-label="Sort logs" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="severity">Errors first</option>
          </select>
        </label>
        {full && (
          <>
            <label>
              Device
              <select
                aria-label="Filter log device"
                value={device}
                onChange={(e) => setDevice(e.target.value)}
              >
                <option value="all">All devices</option>
                {devices.map((id) => (
                  <option key={id} value={id}>
                    {lab.devices.find((d) => d.id === id)?.name ??
                      lab.runs.find((r) => r.deviceId === id)?.deviceName ??
                      id}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Run
              <select
                aria-label="Filter log run"
                value={run}
                onChange={(e) => setRun(e.target.value)}
              >
                <option value="all">All runs</option>
                <option value="selected" disabled={!selectedRun}>
                  Selected report
                </option>
                {lab.runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.deviceName} · {new Date(r.startedAt).toLocaleString()}
                  </option>
                ))}
              </select>
            </label>
            <label>
              From
              <input
                aria-label="Logs from"
                type="datetime-local"
                value={after}
                onChange={(e) => setAfter(e.target.value)}
              />
            </label>
            <label>
              Until
              <input
                aria-label="Logs until"
                type="datetime-local"
                value={before}
                onChange={(e) => setBefore(e.target.value)}
              />
            </label>
            <button
              className="text-button"
              onClick={() => {
                setQuery('');
                setLevel('all');
                setDevice('all');
                setRun('all');
                setAfter('');
                setBefore('');
              }}
            >
              Clear filters
            </button>
          </>
        )}
      </div>
      <p className="event-count">
        {filtered.length} matching events{!full && filtered.length > 12 ? ' · showing 12' : ''} ·
        Older events may not have device or run links.
      </p>
      <div className={`log-stream ${full ? 'tall' : ''}`}>
        {filtered.slice(0, full ? 250 : 12).map((l) => (
          <div className="log-line" key={l.id}>
            <time>{new Date(l.time).toLocaleString()}</time>
            <span className={`log-level ${l.level}`}>{l.level}</span>
            <span>{l.message}</span>
          </div>
        ))}
        {!filtered.length && (
          <p className="empty">
            {lab.logs.length
              ? 'No events match these filters.'
              : 'Waiting for activity. Connect a device to begin.'}
          </p>
        )}
      </div>
    </section>
  );
}
