import { useEffect, useState } from 'react';
import { FiArchive, FiDownload, FiUpload } from 'react-icons/fi';
import { BackupPreview, ServerResponse, WorkspaceArchive, workspaceRequest } from './backend';
import './workspace-backup.css';

const names: Record<string, string> = {
  devices: 'Devices',
  peripherals: 'Peripherals',
  blueprints: 'Blueprints',
  testPlans: 'Test plans',
  scenarios: 'Scenarios',
  validationSuites: 'Validation suites',
  runs: 'Test results',
  suiteRuns: 'Suite reports',
  logs: 'Event logs',
};
export default function WorkspaceBackup({
  enabled,
  serverMode,
  canAdmin,
  revision,
  action,
}: {
  enabled: boolean;
  serverMode: boolean;
  canAdmin: boolean;
  revision: number;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
}) {
  const [archive, setArchive] = useState<WorkspaceArchive>();
  const [filename, setFilename] = useState('');
  const [policy, setPolicy] = useState('keep');
  const [history, setHistory] = useState(true);
  const [preview, setPreview] = useState<BackupPreview>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [open, setOpen] = useState(true);
  const allowed = enabled && canAdmin && serverMode && !busy;
  const stale = !!preview && revision > preview.revision;
  useEffect(() => {
    if (!serverMode) {
      setArchive(undefined);
      setPreview(undefined);
      setFilename('');
    }
  }, [serverMode]);
  async function exportArchive() {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await workspaceRequest<WorkspaceArchive>('/workspace/backup');
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }),
      );
      const a = document.createElement('a');
      a.href = url;
      a.download = `hardware-tester-workspace-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage(
        'Workspace archive downloaded. Keep it somewhere separate from this installation.',
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export failed.');
    } finally {
      setBusy(false);
    }
  }
  async function review() {
    setBusy(true);
    setError('');
    setMessage('');
    setPreview(undefined);
    try {
      const result = await workspaceRequest<{ preview: BackupPreview }>(
        '/workspace/preview',
        'POST',
        { archive, policy, includeHistory: history },
      );
      setPreview(result.preview);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Archive validation failed.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel workspace-backup" aria-label="Workspace backup and restore">
      <header>
        <div>
          <span className="eyebrow">PORTABLE WORKSPACE / ARCHIVE BAY</span>
          <h2>
            <FiArchive /> Backup & restore
          </h2>
          <p>Keep your bench, libraries, and recorded results together.</p>
        </div>
        <button className="text-button" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? 'Collapse backup tools' : 'Expand backup tools'}
        </button>
      </header>
      {open && (
        <div className="backup-body">
          {!serverMode ? (
            <p className="backup-note">
              Connect Flask above to back up the shared workspace. The browser simulator has its own
              local data.
            </p>
          ) : !canAdmin ? (
            <p className="backup-note">
              Workspace backup and import require an administrator account.
            </p>
          ) : (
            !enabled && (
              <p className="backup-note">
                Stop active tests or suites and wait for the workspace connection before using
                backup tools.
              </p>
            )
          )}
          <div className="backup-columns">
            <div>
              <span className="eyebrow">01 / SAVE A COPY</span>
              <h3>Export this workspace</h3>
              <p>
                Includes devices, peripherals, blueprints, plans, scenarios, validation suites, test
                results, suite reports, and event logs.
              </p>
              <p>
                Login accounts, passwords, sessions, API tokens, and server settings stay on this
                installation. Archives contain device endpoints and recorded measurements.
              </p>
              <button
                className="button secondary"
                disabled={!allowed}
                onClick={() => void exportArchive()}
              >
                <FiDownload /> Download workspace archive
              </button>
            </div>
            <div>
              <span className="eyebrow">02 / REVIEW AN ARCHIVE</span>
              <h3>Bring a workspace here</h3>
              <p>
                Imports add entries. Existing definitions are kept; copied conflicts get new IDs and
                their links are updated together. Imported devices remain disconnected.
              </p>
              <label>
                Workspace archive
                <input
                  aria-label="Workspace archive file"
                  type="file"
                  accept=".json,application/json"
                  disabled={!allowed}
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    e.target.value = '';
                    if (!file) return;
                    setBusy(true);
                    setPreview(undefined);
                    setArchive(undefined);
                    setFilename('');
                    setError('');
                    setMessage('');
                    try {
                      if (file.size > 20 * 1024 * 1024)
                        throw new Error('Choose a workspace archive under 20 MB.');
                      const parsed = JSON.parse(await file.text());
                      if (parsed?.format !== 'hardware-tester-workspace' || parsed?.version !== 1)
                        throw new Error('Choose a Hardware Tester workspace archive (version 1).');
                      setArchive(parsed);
                      setFilename(file.name);
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Unable to read this file.');
                    } finally {
                      setBusy(false);
                    }
                  }}
                />
              </label>
              <label>
                Duplicate definitions
                <select
                  aria-label="Workspace conflict policy"
                  disabled={!allowed}
                  value={policy}
                  onChange={(e) => {
                    setPolicy(e.target.value);
                    setPreview(undefined);
                  }}
                >
                  <option value="keep">Keep existing definitions</option>
                  <option value="copy">Import conflicting definitions as copies</option>
                </select>
              </label>
              <label className="backup-checkbox">
                <input
                  type="checkbox"
                  aria-label="Include archived history"
                  disabled={!allowed}
                  checked={history}
                  onChange={(e) => {
                    setHistory(e.target.checked);
                    setPreview(undefined);
                  }}
                />
                Include recorded results and logs
              </label>
              <p>
                Conflicts match saved IDs or definition names. Built-in scenarios and duplicate
                history records are always kept once.
              </p>
              {filename && <p className="backup-filename">Selected: {filename}</p>}
              <button
                className="button secondary"
                disabled={!allowed || !archive}
                onClick={() => void review()}
              >
                Validate & preview import
              </button>
            </div>
          </div>
          {preview && (
            <section className="backup-preview" aria-label="Workspace import preview">
              <header>
                <div>
                  <span className="eyebrow">03 / APPLY REVIEWED IMPORT</span>
                  <h3>{preview.added} entries to add</h3>
                </div>
                <span>REV {preview.revision}</span>
              </header>
              <div className="backup-summary-grid">
                {preview.rows.map((r) => (
                  <article key={r.collection}>
                    <strong>{names[r.collection]}</strong>
                    <b>{r.added}</b>
                    <span>to add · {r.skipped} kept/skipped</span>
                    {r.copied > 0 && <small>{r.copied} imported as copies</small>}
                    {r.trimmed > 0 && (
                      <p className="backup-warning">
                        {r.trimmed} older records fall outside the retained history limit.
                      </p>
                    )}
                    {r.conflicts.length > 0 && (
                      <details>
                        <summary>{r.conflicts.length} conflicts</summary>
                        <ul>
                          {r.conflicts.map((c, i) => (
                            <li key={i}>
                              {c.name} →{' '}
                              {policy === 'keep' ? `keep ${c.existingName}` : 'add a new copy'}
                            </li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </article>
                ))}
              </div>
              {preview.warnings.map((w, i) => (
                <p className="backup-warning" key={i}>
                  {w}
                </p>
              ))}
              <p>
                Import changes no existing definitions. Current history limits still apply: 100 test
                results, 10 suite reports, and 250 event logs. One import event is recorded in the
                log.
              </p>
              {stale && (
                <p role="alert" className="backup-warning">
                  The workspace changed after this preview. Validate and preview again before
                  importing.
                </p>
              )}
              <div className="backup-apply">
                <button
                  className="button secondary"
                  disabled={!allowed}
                  onClick={() => {
                    setArchive(undefined);
                    setPreview(undefined);
                    setFilename('');
                  }}
                >
                  Cancel import
                </button>
                <button
                  className="button primary"
                  disabled={!allowed || stale || preview.added === 0}
                  onClick={async () => {
                    setBusy(true);
                    setError('');
                    try {
                      const result = await action('/workspace/import', 'POST', {
                        archive,
                        policy,
                        includeHistory: history,
                        revision: preview.revision,
                        digest: preview.digest,
                      });
                      if (result) {
                        setMessage(
                          `Workspace import complete. ${preview.added} entries added; imported devices are disconnected.`,
                        );
                        setArchive(undefined);
                        setFilename('');
                      } else
                        setError(
                          'Import was not applied. Check the workspace message and preview again.',
                        );
                    } finally {
                      setPreview(undefined);
                      setBusy(false);
                    }
                  }}
                >
                  <FiUpload /> Apply workspace import
                </button>
              </div>
            </section>
          )}
          {busy && <p role="status">Working with the workspace archive…</p>}
          {error && (
            <p role="alert" className="backup-warning">
              {error}
            </p>
          )}
          {message && (
            <p role="status" className="backup-success">
              {message}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
