import { type FormEvent, useEffect, useRef, useState } from 'react';
import { FiRefreshCw, FiTrash2, FiUpload } from 'react-icons/fi';
import { NavLink } from 'react-router-dom';
import { workspaceRequest } from './backend';
import './pi-inventories.css';

interface CheckOption {
  id: string;
  name: string;
}

type Observation =
  | string
  | null
  | {
      loadState: string;
      activeState: string;
      unitFileState: string | null;
    };

interface DriftItem {
  group: string;
  name: string;
  before: Observation;
  after: Observation;
  status: 'changed' | 'unchanged' | 'unavailable';
}

interface PiInventory {
  id: string;
  name: string;
  inventory: {
    schemaVersion: 1 | 2;
    capturedAt: string;
    model: string;
    architecture: string;
    kernel: string;
    osId: string;
    osVersion: string;
    memoryMiB: number;
    interfaces: string[];
    observations?: Record<string, Record<string, Observation>>;
  };
  recommendedChecks: CheckOption[];
  specializedChecks: CheckOption[];
}

interface CheckResult {
  name: string;
  expected: string;
  actual: string;
  passed: boolean;
}

const inventoryPath = '/pi-inventories';
const observationNames: Record<string, string> = {
  osId: 'OS ID',
  osVersion: 'OS version',
  kernel: 'Kernel',
  videoCoreRevision: 'VideoCore revision',
  startElfSha256: 'Installed start.elf SHA-256',
  bootConfigSha256: 'Boot config SHA-256',
  bootCmdlineSha256: 'Boot command line SHA-256',
};
const maxCustomChecks = 10;
const interfaceCategories = [
  'bluetooth',
  'ethernet',
  'gpio',
  'i2c',
  'serial',
  'spi',
  'usb',
  'wifi',
];
const customFields = {
  osId: 'Operating system ID',
  osVersion: 'Operating system version',
  architecture: 'Architecture',
  kernel: 'Kernel release',
  interface: 'Recorded interface',
};

type CustomCheck = { id: number; field: keyof typeof customFields; value: string };

function observationText(value: Observation) {
  if (value === null) return 'Unavailable';
  if (typeof value === 'string') return value;
  return [value.loadState, value.activeState, value.unitFileState].filter(Boolean).join(' · ');
}

function PiProvisioning({
  entry,
  inventories,
  enabled,
  canOperate,
}: {
  entry: PiInventory;
  inventories: PiInventory[];
  enabled: boolean;
  canOperate: boolean;
}) {
  const [baseline, setBaseline] = useState('');
  const [drift, setDrift] = useState<DriftItem[]>();
  const [plan, setPlan] = useState<{ release: string }>();
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const candidates = inventories.filter(
    ({ id, inventory }) =>
      id !== entry.id &&
      inventory.model === entry.inventory.model &&
      inventory.architecture === entry.inventory.architecture &&
      Date.parse(inventory.capturedAt) <= Date.parse(entry.inventory.capturedAt),
  );
  const path = `${inventoryPath}/${entry.id}`;

  async function perform(action: () => Promise<void>) {
    setError('');
    setPending(true);
    try {
      await action();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'The provisioning request failed.');
    } finally {
      setPending(false);
    }
  }

  function generatePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = new FormData(event.currentTarget).get('manifest');
    setPlan(undefined);
    void perform(async () => {
      if (!(file instanceof File) || !file.size || file.size > 32 * 1024) {
        throw new Error('Choose a provisioning manifest JSON file up to 32 KiB.');
      }
      let manifest: unknown;
      try {
        manifest = JSON.parse(await file.text());
      } catch {
        throw new Error('The provisioning manifest must contain valid JSON.');
      }
      const result = await workspaceRequest<{ plan: { release: string } }>(
        `${path}/provisioning-plan`,
        'POST',
        { manifest },
      );
      setPlan(result.plan);
    });
  }

  function downloadPlan() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' }),
    );
    const link = document.createElement('a');
    link.href = url;
    link.download = 'pi3b-provisioning-plan.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  return (
    <section className="panel settings-panel pi-panel pi-provisioning">
      <h2>Provisioning and drift</h2>
      {error && <p role="alert">{error}</p>}
      <details>
        <summary>Firmware, configuration and services</summary>
        {entry.inventory.observations ? (
          <dl>
            {Object.values(entry.inventory.observations).flatMap((group) =>
              Object.entries(group).map(([name, value]) => (
                <div key={name}>
                  <dt>{observationNames[name] ?? name}</dt>
                  <dd>{observationText(value)}</dd>
                </div>
              )),
            )}
          </dl>
        ) : (
          <p>This capture predates firmware, configuration, and service observations.</p>
        )}
      </details>
      {candidates.length ? (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setDrift(undefined);
            void perform(async () => {
              const result = await workspaceRequest<{ items: DriftItem[] }>(
                `${path}/drift?baselineId=${encodeURIComponent(baseline)}`,
              );
              setDrift(result.items);
            });
          }}
        >
          <fieldset disabled={!enabled || pending}>
            <label>
              Baseline capture from the same Pi
              <select
                required
                value={baseline}
                onChange={(event) => {
                  setBaseline(event.target.value);
                  setDrift(undefined);
                }}
              >
                <option value="">Choose a baseline</option>
                {candidates.map(({ id, name, inventory }) => (
                  <option key={id} value={id}>
                    {name} · {new Date(inventory.capturedAt).toLocaleString()}
                  </option>
                ))}
              </select>
            </label>
            <button className="button secondary">Compare captures</button>
          </fieldset>
        </form>
      ) : (
        <p>Import an earlier capture from this Pi to compare drift.</p>
      )}
      {drift && (
        <div className="pi-check-results" aria-label="Inventory drift results">
          <p role="status">
            {drift.filter(({ status }) => status === 'changed').length} changed ·{' '}
            {drift.filter(({ status }) => status === 'unavailable').length} unavailable
          </p>
          <ol>
            {drift
              .filter(({ status }) => status !== 'unchanged')
              .map((item) => (
                <li key={item.name}>
                  <strong>{observationNames[item.name] ?? item.name}</strong>
                  <p>
                    {observationText(item.before)} → {observationText(item.after)}
                  </p>
                </li>
              ))}
          </ol>
        </div>
      )}
      {canOperate && (
        <form onSubmit={generatePlan}>
          <fieldset disabled={!enabled || pending}>
            <h3>Raspberry Pi 3 Model B · 64-bit</h3>
            <label>
              Approved release manifest
              <input
                type="file"
                name="manifest"
                accept=".json,application/json"
                required
                onChange={() => setPlan(undefined)}
              />
            </label>
            <button className="button primary">Generate provisioning plan</button>
          </fieldset>
          {plan && (
            <p role="status">
              {plan.release} · Plan ready for local image verification.{' '}
              <button type="button" className="button secondary" onClick={downloadPlan}>
                Download plan
              </button>
            </p>
          )}
        </form>
      )}
    </section>
  );
}

function InventoryChecks({
  entry,
  enabled,
  runChecks,
  results,
}: {
  entry: PiInventory;
  enabled: boolean;
  runChecks: (checkIds: string[], customChecks: CustomCheck[]) => void;
  results: CheckResult[];
}) {
  const [checkIds, setCheckIds] = useState(() => entry.recommendedChecks.map(({ id }) => id));
  const [customChecks, setCustomChecks] = useState<CustomCheck[]>([]);
  const nextCustomId = useRef(0);
  const groups = [
    { name: 'Recommended checks', checks: entry.recommendedChecks },
    { name: 'Specialized checks', checks: entry.specializedChecks },
  ];
  const passed = results.filter((result) => result.passed).length;

  function updateCustomCheck(id: number, update: Partial<Omit<CustomCheck, 'id'>>) {
    setCustomChecks((previous) =>
      previous.map((check) => (check.id === id ? { ...check, ...update } : check)),
    );
  }

  return (
    <section className="panel settings-panel pi-panel" aria-label="Inventory checks">
      <h2>Inventory checks</h2>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (enabled) runChecks(checkIds, customChecks);
        }}
      >
        <fieldset
          className="pi-check-options"
          disabled={!enabled}
          aria-label="Choose inventory checks"
        >
          {groups.map((group) => (
            <div key={group.name}>
              <h3>{group.name}</h3>
              {group.checks.length ? (
                group.checks.map((check) => (
                  <label className="pi-checkbox" key={check.id}>
                    <input
                      type="checkbox"
                      checked={checkIds.includes(check.id)}
                      onChange={(event) => {
                        const checked = event.currentTarget.checked;
                        setCheckIds((previous) =>
                          checked
                            ? [...previous, check.id]
                            : previous.filter((id) => id !== check.id),
                        );
                      }}
                    />
                    {check.name}
                  </label>
                ))
              ) : (
                <p>No checks available for this capture.</p>
              )}
            </div>
          ))}
          <div>
            <h3>Custom checks</h3>
            {customChecks.length > 0 && (
              <p>Compare a captured value or require an interface to appear in the inventory.</p>
            )}
            {customChecks.map((check) => (
              <div className="pi-custom-check" key={check.id}>
                <label>
                  Field
                  <select
                    value={check.field}
                    onChange={(event) =>
                      updateCustomCheck(check.id, {
                        field: event.currentTarget.value as CustomCheck['field'],
                        value: '',
                      })
                    }
                  >
                    {Object.entries(customFields).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Expected value
                  {check.field === 'interface' ? (
                    <select
                      required
                      value={check.value}
                      onChange={(event) =>
                        updateCustomCheck(check.id, { value: event.currentTarget.value })
                      }
                    >
                      <option value="">Choose an interface</option>
                      {interfaceCategories.map((category) => (
                        <option key={category}>{category}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      required
                      maxLength={160}
                      value={check.value}
                      onChange={(event) =>
                        updateCustomCheck(check.id, { value: event.currentTarget.value })
                      }
                    />
                  )}
                </label>
                <button
                  type="button"
                  className="icon-button"
                  aria-label={`Remove custom check for ${customFields[check.field]}`}
                  onClick={() =>
                    setCustomChecks((checks) => checks.filter(({ id }) => id !== check.id))
                  }
                >
                  <FiTrash2 />
                </button>
              </div>
            ))}
            <button
              type="button"
              className="button secondary"
              disabled={customChecks.length >= maxCustomChecks}
              onClick={() => {
                const id = nextCustomId.current++;
                setCustomChecks((checks) => [...checks, { id, field: 'osId', value: '' }]);
              }}
            >
              Add custom check
            </button>
          </div>
          <button
            className="button primary"
            disabled={
              !(checkIds.length || customChecks.length) ||
              customChecks.some((check) => !check.value.trim())
            }
          >
            Run inventory checks
          </button>
        </fieldset>
      </form>
      <div className="pi-check-results" aria-label="Inventory check results">
        <div role="status">
          {results.length > 0 && (
            <h3>
              {passed} of {results.length} checks passed
            </h3>
          )}
        </div>
        {results.length > 0 && (
          <ol>
            {results.map((result, index) => (
              <li key={index}>
                <div>
                  <strong>{result.name}</strong>
                  <span className={`status status-${result.passed ? 'passed' : 'failed'}`}>
                    {result.passed ? 'Passed' : 'Failed'}
                  </span>
                </div>
                <p>Expected · {result.expected}</p>
                <p>Observed · {result.actual}</p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}

export default function PiInventories({
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
  const [inventories, setInventories] = useState<PiInventory[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [report, setReport] = useState<{ id: string; checks: CheckResult[] }>();
  const ready = serverMode && serverReady;
  const enabled = ready && !loading && !pending;
  const entry = inventories.find(({ id }) => id === selectedId) ?? inventories[0];

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    setLoading(true);
    setError('');
    void workspaceRequest<{ inventories: PiInventory[] }>(inventoryPath)
      .then(({ inventories }) => {
        if (!cancelled) setInventories(inventories);
      })
      .catch((error: unknown) => {
        if (!cancelled)
          setError(error instanceof Error ? error.message : 'Could not load Pi inventories.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ready, refresh]);

  async function perform(action: () => Promise<void>) {
    setPending(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Request failed.');
    } finally {
      setPending(false);
    }
  }

  function importInventory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!enabled || !canAdmin) return;
    const form = event.currentTarget;
    const fields = new FormData(form);
    const file = fields.get('inventory');
    const name = String(fields.get('name') ?? '').trim();
    void perform(async () => {
      if (!name) throw new Error('Enter a name for this inventory.');
      if (!(file instanceof File) || !file.size)
        throw new Error('Choose a Pi inventory JSON file.');
      if (file.size > 32 * 1024) throw new Error('Choose an inventory file up to 32 KiB.');
      let inventory: unknown;
      try {
        inventory = JSON.parse(await file.text());
      } catch {
        throw new Error('The inventory file must contain valid JSON.');
      }
      const result = await workspaceRequest<{ inventories: PiInventory[] }>(inventoryPath, 'POST', {
        name,
        inventory,
      });
      const created = result.inventories.find(
        (candidate) =>
          candidate.name === name && !inventories.some(({ id }) => id === candidate.id),
      );
      if (created) setSelectedId(created.id);
      setInventories(result.inventories);
      setNotice('Inventory imported.');
      form.reset();
    });
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Raspberry Pi inventories</h1>
          <p>Review captured operating system and hardware details and run checks against them.</p>
        </div>
      </div>
      {!serverMode ? (
        <p className="backend-warning">
          <NavLink to="/settings">Connect Flask in workspace settings</NavLink> to access
          inventories.
        </p>
      ) : !serverReady ? (
        <p role="status">Waiting for the Flask workspace…</p>
      ) : (
        <>
          {error && (
            <p className="backend-warning" role="alert">
              {error}
            </p>
          )}
          {notice && <p role="status">{notice}</p>}
          <div className="pi-library">
            <section className="panel settings-panel pi-panel">
              <div className="pi-panel-heading">
                <h2>Saved inventories</h2>
                <button
                  type="button"
                  className="icon-button"
                  aria-label="Refresh inventories"
                  title="Refresh inventories"
                  disabled={!enabled}
                  onClick={() => setRefresh((previous) => previous + 1)}
                >
                  <FiRefreshCw />
                </button>
              </div>
              {loading ? (
                <p role="status">Loading inventories…</p>
              ) : inventories.length ? (
                <label>
                  Inventory
                  <select
                    value={entry?.id}
                    onChange={(event) => setSelectedId(event.target.value)}
                    disabled={pending}
                  >
                    {inventories.map((saved) => (
                      <option key={saved.id} value={saved.id}>
                        {saved.name}
                      </option>
                    ))}
                  </select>
                </label>
              ) : (
                <p>No saved inventories.</p>
              )}
              {canAdmin && (
                <form className="pi-import" onSubmit={importInventory}>
                  <h3>Import a capture</h3>
                  <p>Choose the JSON file produced by the Raspberry Pi inventory collector.</p>
                  <fieldset disabled={!enabled} aria-label="Import inventory">
                    <label>
                      Inventory name
                      <input
                        required
                        name="name"
                        maxLength={80}
                        placeholder="Ecolab test controller"
                      />
                    </label>
                    <label>
                      Inventory JSON file
                      <input
                        required
                        name="inventory"
                        type="file"
                        accept=".json,application/json"
                      />
                    </label>
                    <button className="button primary">
                      <FiUpload /> Import inventory
                    </button>
                  </fieldset>
                </form>
              )}
            </section>
            {entry && (
              <div>
                <section className="panel settings-panel pi-panel">
                  <div className="pi-panel-heading">
                    <h2>{entry.name}</h2>
                    {canAdmin && (
                      <button
                        type="button"
                        className="icon-button"
                        aria-label="Delete selected inventory"
                        title="Delete selected inventory"
                        disabled={!enabled}
                        onClick={() => {
                          if (!confirm(`Delete saved inventory ${entry.name}?`)) return;
                          void perform(async () => {
                            const result = await workspaceRequest<{ inventories: PiInventory[] }>(
                              `${inventoryPath}/${entry.id}`,
                              'DELETE',
                            );
                            setInventories(result.inventories);
                            setReport(undefined);
                            setNotice('Inventory deleted.');
                          });
                        }}
                      >
                        <FiTrash2 />
                      </button>
                    )}
                  </div>
                  <dl>
                    {Object.entries({
                      Model: entry.inventory.model,
                      Architecture: entry.inventory.architecture,
                      'OS ID': entry.inventory.osId,
                      'OS version': entry.inventory.osVersion,
                      Kernel: entry.inventory.kernel,
                      Memory: `${entry.inventory.memoryMiB.toLocaleString()} MiB`,
                      Interfaces: entry.inventory.interfaces.join(', ') || 'None recorded',
                      Captured: new Date(entry.inventory.capturedAt).toLocaleString(),
                    }).map(([label, value]) => (
                      <div key={label}>
                        <dt>{label}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                  </dl>
                </section>
                <PiProvisioning
                  key={`provisioning-${entry.id}`}
                  entry={entry}
                  inventories={inventories}
                  enabled={enabled}
                  canOperate={canOperate}
                />
                {!canOperate && <p>An operator or administrator can run inventory checks.</p>}
                <InventoryChecks
                  key={entry.id}
                  entry={entry}
                  enabled={enabled && canOperate}
                  results={report?.id === entry.id ? report.checks : []}
                  runChecks={(checkIds, customChecks) => {
                    setReport(undefined);
                    void perform(async () => {
                      const { checks } = await workspaceRequest<{ checks: CheckResult[] }>(
                        `${inventoryPath}/${entry.id}/checks`,
                        'POST',
                        {
                          checkIds,
                          customChecks: customChecks.map(({ field, value }) => ({
                            field,
                            value: value.trim(),
                          })),
                        },
                      );
                      setReport({ id: entry.id, checks });
                    });
                  }}
                />
              </div>
            )}
          </div>
        </>
      )}
      <p className="pi-fidelity">
        Inventory checks evaluate the saved capture. Verify OS boot separately in QEMU, and use a
        physical bench for checks that depend on actual peripherals or timing.
      </p>
    </>
  );
}
