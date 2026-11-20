import { FormEvent, useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { fetchFirmwareBinary, workspaceRequest } from './backend';
import FirmwareInventory, { type InventorySummary } from './FirmwareInventory';
import './firmware-library.css';

interface Artifact {
  schemaVersion: number;
  format: 'bin' | 'zip';
  name: string;
  version: string;
  model: string;
  architecture: string;
  sha256: string;
  sizeBytes: number;
  uploadedAt: string;
  uploadedBy: string | null;
  compatibility?: 'mismatch' | 'declaredMatch' | 'inventoryMatch' | 'reviewRequired';
  differences?: string[];
  inventory?: InventorySummary;
}

const compatibilityLabels = {
  declaredMatch: 'Declared match',
  inventoryMatch: 'Board declaration and ELF architecture match',
  mismatch: 'Mismatch',
  reviewRequired: 'Needs review',
};

function artifactKey(item: Artifact) {
  return JSON.stringify([item.name, item.version, item.model, item.architecture]);
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function FirmwareLibrary({
  serverMode,
  serverReady,
  canAdmin,
  canOperate,
}: {
  serverMode: boolean;
  serverReady: boolean;
  canAdmin: boolean;
  canOperate: boolean;
}) {
  const [inventories, setInventories] = useState<{ id: string; name: string }[]>([]);
  const [inventoryId, setInventoryId] = useState('');
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [matchesOnly, setMatchesOnly] = useState(false);
  const [selectedFirmware, setSelectedFirmware] = useState('');
  const [openInventory, setOpenInventory] = useState('');
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  const [pending, setPending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const ready = serverMode && serverReady;

  useEffect(() => {
    if (!ready) return;
    let alive = true;
    void workspaceRequest<{ inventories: { id: string; name: string }[] }>('/pi-inventories')
      .then((data) => {
        if (alive) setInventories(data.inventories);
      })
      .catch((failure: Error) => {
        if (alive) setError(failure.message);
      });
    return () => {
      alive = false;
    };
  }, [ready]);

  useEffect(() => {
    if (!ready) return;
    let alive = true;
    setLoading(true);
    const query = inventoryId ? `?inventoryId=${encodeURIComponent(inventoryId)}` : '';
    void workspaceRequest<{ artifacts: Artifact[] }>(`/firmware${query}`)
      .then((data) => {
        if (alive) setArtifacts(data.artifacts);
      })
      .catch((failure: Error) => {
        if (!alive) return;
        setError(failure.message);
        setArtifacts([]);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [inventoryId, ready, refresh]);

  async function perform(action: () => Promise<void>) {
    setPending(true);
    setError('');
    setStatus('');
    try {
      await action();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Firmware request failed.');
    } finally {
      setPending(false);
    }
  }

  function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    void perform(async () => {
      const file = fields.get('binary');
      if (!(file instanceof File) || !file.size || file.size > 16 * 1024 * 1024) {
        throw new Error('Choose a .bin or .zip file between 1 byte and 16 MiB.');
      }
      const metadata = Object.fromEntries(
        ['name', 'version', 'model', 'architecture', 'sha256'].map((field) => [
          field,
          String(fields.get(field) ?? '').trim(),
        ]),
      );
      const payload = new FormData();
      payload.set('metadata', JSON.stringify(metadata));
      payload.set('binary', file);
      await workspaceRequest('/firmware', 'POST', payload);
      form.reset();
      setSelectedFirmware('');
      setStatus('Firmware saved. SHA-256 verified and inventory recorded.');
      setRefresh((value) => value + 1);
    });
  }

  const compatible =
    inventoryId && !loading
      ? artifacts.filter(
          (item) =>
            item.compatibility === 'declaredMatch' || item.compatibility === 'inventoryMatch',
        )
      : [];
  const selected = compatible.find((item) => artifactKey(item) === selectedFirmware);
  const visible = selected ? [selected] : inventoryId && matchesOnly ? compatible : artifacts;

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Firmware library</h1>
          <p>Inspect firmware files and find candidate releases for a captured board.</p>
        </div>
      </div>
      {!serverMode ? (
        <p className="backend-warning">
          <NavLink to="/settings">Connect Flask in workspace settings</NavLink> to access firmware.
        </p>
      ) : !ready ? (
        <p role="status">Waiting for the Flask workspace…</p>
      ) : (
        <div className="firmware-library">
          {error && (
            <p role="alert" className="backend-warning">
              {error}
            </p>
          )}
          <div role="status">{status}</div>
          {canAdmin && (
            <section className="panel settings-panel">
              <h2>Upload firmware</h2>
              <form onSubmit={upload}>
                <fieldset disabled={pending} className="firmware-fields">
                  <label>
                    Name
                    <input name="name" required maxLength={160} />
                  </label>
                  <label>
                    Version
                    <input name="version" required maxLength={160} />
                  </label>
                  <label>
                    Board model and revision
                    <input name="model" required maxLength={160} />
                  </label>
                  <label>
                    Architecture
                    <input name="architecture" required maxLength={160} />
                  </label>
                  <label>
                    Expected SHA-256
                    <input name="sha256" required pattern="[A-Fa-f0-9]{64}" maxLength={64} />
                  </label>
                  <label>
                    Firmware file (.bin or .zip)
                    <input name="binary" type="file" accept=".bin,.zip" required />
                  </label>
                  <button type="submit" className="button primary">
                    Upload and inspect
                  </button>
                </fieldset>
              </form>
            </section>
          )}
          <section className="panel settings-panel">
            <h2>Saved versions</h2>
            <div className="firmware-fields">
              <label>
                Compare with inventory
                <select
                  value={inventoryId}
                  onChange={(event) => {
                    setError('');
                    setLoading(true);
                    setSelectedFirmware('');
                    setInventoryId(event.target.value);
                  }}
                >
                  <option value="">Choose a Raspberry Pi capture</option>
                  {inventories.map(({ id, name }) => (
                    <option key={id} value={id}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
              {inventoryId && (
                <label>
                  Compatible firmware
                  <select
                    value={selected ? selectedFirmware : ''}
                    disabled={loading || !compatible.length}
                    onChange={(event) => setSelectedFirmware(event.target.value)}
                  >
                    <option value="">
                      {compatible.length ? 'Choose a release' : 'No matching releases'}
                    </option>
                    {compatible.map((item) => (
                      <option value={artifactKey(item)} key={artifactKey(item)}>
                        {item.name} · {item.version} · {item.architecture}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {inventoryId && (
                <label className="firmware-checkbox">
                  <input
                    type="checkbox"
                    checked={matchesOnly}
                    onChange={(event) => setMatchesOnly(event.target.checked)}
                  />
                  Show only matches
                </label>
              )}
            </div>
            {inventoryId && (
              <p>
                Matches use board declarations and available ELF headers. A programmer must verify
                the live target before deployment.
              </p>
            )}
            {loading ? (
              <p role="status">Loading firmware…</p>
            ) : visible.length === 0 ? (
              <p>No firmware versions to display.</p>
            ) : (
              <ul className="firmware-versions">
                {visible.map((item) => (
                  <li key={artifactKey(item)}>
                    <h3>
                      {item.name} · {item.version}
                    </h3>
                    <p>
                      {item.model} · {item.architecture} · {item.format.toUpperCase()} ·{' '}
                      {item.sizeBytes.toLocaleString()} bytes
                    </p>
                    <p>
                      <code>{item.sha256}</code>
                    </p>
                    {item.compatibility && (
                      <p>
                        {compatibilityLabels[item.compatibility]}
                        {!!item.differences?.length && ` (${item.differences.join(', ')})`}
                      </p>
                    )}
                    <div className="firmware-actions">
                      {item.inventory && (
                        <button
                          className="button"
                          type="button"
                          aria-expanded={openInventory === artifactKey(item)}
                          onClick={() =>
                            setOpenInventory(
                              openInventory === artifactKey(item) ? '' : artifactKey(item),
                            )
                          }
                        >
                          {openInventory === artifactKey(item)
                            ? 'Hide inventory'
                            : 'Inspect release'}
                        </button>
                      )}
                      {canOperate && (
                        <>
                          <button
                            className="button"
                            disabled={pending}
                            onClick={() =>
                              void perform(async () => {
                                saveBlob(
                                  await fetchFirmwareBinary(item.sha256, item.format),
                                  `${item.sha256}.${item.format}`,
                                );
                              })
                            }
                          >
                            {item.format === 'bin' ? 'Download binary' : 'Download bundle'}
                          </button>
                          <button
                            className="button"
                            disabled={pending}
                            onClick={() => {
                              const {
                                schemaVersion,
                                format,
                                name,
                                version,
                                model,
                                architecture,
                                sha256,
                                sizeBytes,
                              } = item;
                              saveBlob(
                                new Blob(
                                  [
                                    JSON.stringify(
                                      {
                                        schemaVersion,
                                        format,
                                        name,
                                        version,
                                        model,
                                        architecture,
                                        sha256,
                                        sizeBytes,
                                      },
                                      null,
                                      2,
                                    ),
                                  ],
                                  { type: 'application/json' },
                                ),
                                `${sha256}.json`,
                              );
                            }}
                          >
                            Download manifest
                          </button>
                        </>
                      )}
                    </div>
                    {!item.inventory && <p>Reupload this older release to add its inventory.</p>}
                    {item.inventory && openInventory === artifactKey(item) && (
                      <FirmwareInventory
                        key={item.sha256}
                        digest={item.sha256}
                        saveFile={saveBlob}
                      />
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </>
  );
}
