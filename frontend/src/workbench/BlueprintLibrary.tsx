import SavedBlueprintLibrary, { BlueprintPreview } from './SavedBlueprintLibrary';
import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Blueprint, ServerResponse } from './backend';
import { LabState } from './simulator';

export default function BlueprintLibrary({
  lab,
  enabled,
  action,
}: {
  lab: LabState;
  enabled: boolean;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
}) {
  const [source, setSource] = useState('');
  const [preview, setPreview] = useState<Blueprint>();
  const [revealId, setRevealId] = useState('');
  const [revealVersion, setRevealVersion] = useState(0);
  function reveal(result: ServerResponse) {
    setRevealId(result.blueprintId ?? '');
    setRevealVersion((n) => n + 1);
  }
  const [name, setName] = useState('My bench');
  const [error, setError] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [pName, setPName] = useState('Operating limits');
  const [pType, setPType] = useState('Sensor');
  const [properties, setProperties] = useState('{"threshold":{"min":0,"max":50}}');
  const [edit, setEdit] = useState<{ id: string; version: number }>();
  async function safely(fn: () => Promise<unknown>) {
    setError('');
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Invalid configuration.');
    }
  }
  function exportBlueprint(b: Blueprint) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(b.configuration, null, 2)], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'blueprint.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">YOUR ORIGINAL CONFIGURATIONS</span>
          <h1>Blueprint library</h1>
          <p>Reuse controller configurations and attach peripheral settings to your bench.</p>
        </div>
      </div>
      {!enabled && (
        <p className="backend-warning">
          This library uses Flask persistence.{' '}
          <NavLink to="/settings">Connect Flask in workspace settings</NavLink>, or wait for the
          active test to finish.
        </p>
      )}
      {error && (
        <p className="backend-warning" role="alert">
          {error}
        </p>
      )}
      <div className="blueprint-management-grid">
        <section className="panel settings-panel">
          <h2>Import controller blueprint</h2>
          <p>
            Supports your original peripherals and controller.peripherals formats, plus exported
            bench blueprints. Supported profiles are temperature, valve, and relay.
          </p>
          <label>
            JSON file
            <input
              aria-label="Blueprint JSON file"
              type="file"
              accept=".json,application/json"
              disabled={!enabled}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file)
                  void safely(async () => {
                    if (file.size > 100000)
                      throw new Error('Choose a JSON file smaller than 100 KB.');
                    setSource(await file.text());
                    setPreview(undefined);
                  });
              }}
            />
          </label>
          <label>
            Blueprint JSON
            <textarea
              aria-label="Blueprint JSON"
              rows={8}
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                setPreview(undefined);
              }}
            />
          </label>
          <button
            className="button secondary"
            disabled={!enabled || !source}
            onClick={() =>
              void safely(async () => {
                const result = await action('/blueprints/preview', 'POST', {
                  configuration: JSON.parse(source),
                });
                setPreview(result?.preview);
              })
            }
          >
            Preview import
          </button>
          {preview && (
            <div>
              <h3>
                {preview.name} · {preview.devices.length} devices
              </h3>
              <BlueprintPreview blueprint={preview} showNotes />
              <button
                className="button primary"
                disabled={!enabled}
                onClick={() =>
                  void safely(async () => {
                    const result = await action('/blueprints', 'POST', {
                      configuration: JSON.parse(source),
                    });
                    if (result) {
                      reveal(result);
                      setSource('');
                      setPreview(undefined);
                    }
                  })
                }
              >
                Save blueprint
              </button>
            </div>
          )}
          <h2>Capture current bench</h2>
          <p>
            Saves device profiles and attached peripherals. Applying a blueprint adds disconnected
            simulations; credentials and live transport settings are excluded.
          </p>
          <label>
            Blueprint name
            <input
              aria-label="Capture blueprint name"
              maxLength={100}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <button
            className="button secondary"
            disabled={!enabled || !lab.devices.length || !name.trim()}
            onClick={async () => {
              const result = await action('/blueprints/capture', 'POST', { name });
              if (result) reveal(result);
            }}
          >
            Save current bench
          </button>
        </section>
        <SavedBlueprintLibrary
          blueprints={lab.blueprints ?? []}
          enabled={enabled}
          revealId={revealId}
          revealVersion={revealVersion}
          onApply={(b) => void action(`/blueprints/${b.id}/apply`)}
          onExport={exportBlueprint}
          onDelete={(b) => {
            if (
              confirm(`Delete saved blueprint ${b.name}? Devices already added stay on the bench.`)
            )
              void action(`/blueprints/${b.id}`, 'DELETE');
          }}
        />
      </div>
      <section className="panel settings-panel">
        <h2>Peripheral settings</h2>
        <p>
          The original peripheral service now manages these records. Thresholds are used by Flask
          operating-range checks: a number sets the maximum; an object sets min and/or max. Other
          properties remain configuration metadata.
        </p>
        <div className="catalog-grid">
          <div>
            <label>
              Device
              <select
                aria-label="Peripheral device"
                disabled={!!edit}
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
              >
                <option value="">Select a device</option>
                {lab.devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Name
              <input
                aria-label="Peripheral name"
                disabled={!!edit}
                value={pName}
                onChange={(e) => setPName(e.target.value)}
                maxLength={100}
              />
            </label>
            <label>
              Type
              <input
                aria-label="Peripheral type"
                disabled={!!edit}
                value={pType}
                onChange={(e) => setPType(e.target.value)}
                maxLength={100}
              />
            </label>
            <label>
              Properties JSON
              <textarea
                aria-label="Peripheral properties"
                rows={5}
                value={properties}
                onChange={(e) => setProperties(e.target.value)}
              />
            </label>
            <div className="inline">
              <button
                className="button primary"
                disabled={!enabled || !deviceId || !pName.trim() || !pType.trim()}
                onClick={() =>
                  void safely(async () => {
                    const result = await action(
                      edit ? `/peripherals/${edit.id}` : '/peripherals',
                      edit ? 'PATCH' : 'POST',
                      {
                        name: pName,
                        type: pType,
                        device_id: deviceId,
                        properties: JSON.parse(properties),
                        version: edit?.version,
                      },
                    );
                    if (result) setEdit(undefined);
                  })
                }
              >
                {edit ? 'Save properties' : 'Add peripheral'}
              </button>
              {edit && (
                <button className="button secondary" onClick={() => setEdit(undefined)}>
                  Cancel edit
                </button>
              )}
            </div>
          </div>
          <div>
            {lab.peripherals?.map((p) => (
              <article className="catalog-item" key={p.id}>
                <h3>{p.name}</h3>
                <p>
                  {lab.devices.find((d) => d.id === p.device_id)?.name} · {p.type}
                </p>
                <pre>{JSON.stringify(p.properties, null, 2)}</pre>
                <div className="inline">
                  <button
                    className="button secondary"
                    disabled={!enabled}
                    onClick={() => {
                      setEdit({ id: p.id, version: p.version });
                      setDeviceId(p.device_id);
                      setPName(p.name);
                      setPType(p.type);
                      setProperties(JSON.stringify(p.properties, null, 2));
                    }}
                  >
                    Edit properties
                  </button>
                  <button
                    className="button secondary danger"
                    disabled={!enabled}
                    onClick={() => {
                      if (confirm(`Remove peripheral ${p.name}?`))
                        void action(`/peripherals/${p.id}`, 'DELETE', { version: p.version });
                    }}
                  >
                    Remove
                  </button>
                </div>
              </article>
            ))}
            {!lab.peripherals?.length && (
              <p className="empty">No peripheral settings attached yet.</p>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
