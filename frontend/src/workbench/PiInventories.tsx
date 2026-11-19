import { type FormEvent, useEffect, useRef, useState } from 'react';
import { FiRefreshCw, FiTrash2, FiUpload } from 'react-icons/fi';
import { NavLink } from 'react-router-dom';
import { workspaceRequest } from './backend';
import './pi-inventories.css';

interface CheckOption {
  id: string;
  name: string;
}

interface PiInventory {
  id: string;
  name: string;
  inventory: {
    schemaVersion: 1;
    capturedAt: string;
    model: string;
    architecture: string;
    kernel: string;
    osId: string;
    osVersion: string;
    memoryMiB: number;
    interfaces: string[];
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
