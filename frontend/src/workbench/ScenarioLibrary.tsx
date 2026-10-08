import SavedScenarioLibrary, { scenarioBehaviors } from './SavedScenarioLibrary';
import { FiChevronDown } from 'react-icons/fi';
import { useEffect, useRef, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Device, LabState } from './simulator';
import { ServerResponse } from './backend';
import './scenarios.css';
export interface ScenarioFrame {
  behavior: 'healthy' | 'timeout' | 'out-of-range' | 'delay';
  count: number;
  delayMs?: number;
}
export interface Scenario {
  id: string;
  name: string;
  description: string;
  version: number;
  builtin: boolean;
  frames: ScenarioFrame[];
}
const behaviors = scenarioBehaviors;
export function ScenarioControls({
  device,
  lab,
  enabled,
  serverMode,
  action,
}: {
  device: Device;
  lab: LabState;
  enabled: boolean;
  serverMode: boolean;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
}) {
  const [chosen, setChosen] = useState('');
  const scenario = device.scenario;
  const total = scenario?.frames.reduce((n, f) => n + f.count, 0) ?? 0;
  return (
    <section className="inspector-section scenario-controls" aria-label="Emulator scenario">
      <span className="eyebrow">REUSABLE EMULATION</span>
      {!serverMode ? (
        <p className="helper">
          Scenario sequences run in the shared Flask simulator. Connect Flask in{' '}
          <NavLink to="/settings">Settings</NavLink>.
        </p>
      ) : device.adapter !== 'simulation' ? (
        <p className="helper">Scenarios apply only to simulated devices.</p>
      ) : (
        <>
          <label>
            Scenario
            <select
              aria-label="Choose emulator scenario"
              value={chosen}
              onChange={(e) => setChosen(e.target.value)}
              disabled={!enabled}
            >
              <option value="">Choose a scenario…</option>
              {lab.scenarios?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} · v{s.version}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button secondary full"
            disabled={!enabled || !lab.scenarios?.some((s) => s.id === chosen)}
            onClick={() =>
              void action(`/devices/${device.id}/scenario`, 'POST', { scenarioId: chosen })
            }
          >
            Apply scenario
          </button>
          {scenario && (
            <div className="scenario-running">
              <strong>
                {scenario.name} · v{scenario.version}
              </strong>
              <p>
                {Math.min(device.scenarioCursor ?? 0, total)} / {total} staged reads consumed
              </p>
              <div className="scenario-progress">
                <i
                  style={{
                    width: `${total ? (Math.min(device.scenarioCursor ?? 0, total) / total) * 100 : 0}%`,
                  }}
                />
              </div>
              <p>
                {(device.scenarioCursor ?? 0) >= total
                  ? 'Final response behavior now repeats.'
                  : 'The next diagnostic or test read advances this sequence.'}
              </p>
              <div className="scenario-buttons">
                <button
                  className="button secondary"
                  disabled={!enabled}
                  onClick={() =>
                    void action(`/devices/${device.id}/scenario`, 'POST', { restart: true })
                  }
                >
                  Restart sequence
                </button>
                <button
                  className="text-button"
                  disabled={!enabled}
                  onClick={() =>
                    void action(`/devices/${device.id}/scenario`, 'POST', { scenarioId: null })
                  }
                >
                  Clear scenario
                </button>
              </div>
            </div>
          )}
          <p className="helper">
            Reads include command acknowledgements. Runs continue at the current position; restart
            before repeating an experiment. Background polling does not consume stages. Editing or
            deleting a saved scenario leaves its applied snapshot unchanged.
          </p>
          <NavLink className="text-button" to="/scenarios">
            Open scenario library
          </NavLink>
        </>
      )}
    </section>
  );
}
export default function ScenarioLibrary({
  lab,
  enabled,
  serverMode,
  action,
}: {
  lab: LabState;
  enabled: boolean;
  serverMode: boolean;
  action: (path: string, method?: string, data?: unknown) => Promise<ServerResponse | undefined>;
}) {
  const [name, setName] = useState('My recovery scenario');
  const [description, setDescription] = useState('');
  const [frames, setFrames] = useState<ScenarioFrame[]>([
    { behavior: 'timeout', count: 2 },
    { behavior: 'healthy', count: 1 },
  ]);
  const [editing, setEditing] = useState<Scenario>();
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<Set<number>>(new Set([0]));
  const [revealId, setRevealId] = useState('');
  const [revealVersion, setRevealVersion] = useState(0);
  const [editorFocus, setEditorFocus] = useState(0);
  const editorHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (editorFocus) editorHeading.current?.focus();
  }, [editorFocus]);
  const stageErrors = frames.map((f) =>
    !Number.isInteger(f.count) || f.count < 1 || f.count > 100
      ? 'Use 1–100 whole read attempts.'
      : f.behavior === 'delay' &&
          (!Number.isFinite(f.delayMs) || f.delayMs! < 0 || f.delayMs! > 2000)
        ? 'Delay must be 0–2000 milliseconds.'
        : '',
  );
  function toggleStage(i: number) {
    setExpanded((previous) => {
      const next = new Set(previous);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
  }
  const total = frames.reduce((n, f) => n + f.count, 0);
  const valid =
    !!name.trim() &&
    frames.every(
      (f) =>
        Number.isInteger(f.count) &&
        f.count >= 1 &&
        f.count <= 100 &&
        (f.behavior !== 'delay' ||
          (Number.isFinite(f.delayMs) && f.delayMs! >= 0 && f.delayMs! <= 2000)),
    ) &&
    total <= 200;
  function load(s: Scenario, copy = false) {
    setEditorFocus((previous) => previous + 1);
    setExpanded(new Set());
    setError('');
    setEditing(copy ? undefined : s);
    setName(copy ? `${s.name.slice(0, 90)} copy` : s.name);
    setDescription(s.description);
    setFrames(s.frames.map((f) => ({ ...f })));
  }
  function reset() {
    setExpanded(new Set([0]));
    setError('');
    setEditing(undefined);
    setName('My recovery scenario');
    setDescription('');
    setFrames([{ behavior: 'healthy', count: 1 }]);
  }
  function update(i: number, p: Partial<ScenarioFrame>) {
    setFrames((prev) => prev.map((f, j) => (i === j ? { ...f, ...p } : f)));
  }
  function exportScenario(s: Scenario) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(s, null, 2)], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'emulator-scenario.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <span className="eyebrow">REPEATABLE FAILURE & RECOVERY</span>
          <h1>Emulator scenarios</h1>
          <p>Give simulated devices a response sequence you can reproduce.</p>
        </div>
      </div>
      {!serverMode && (
        <p className="backend-warning">
          Saved scenarios use the Flask workspace.{' '}
          <NavLink to="/settings">Connect Flask in Settings</NavLink>.
        </p>
      )}
      <div className="scenario-management-grid">
        <section className="panel settings-panel scenario-editor" aria-label="Scenario editor">
          <h2 ref={editorHeading} tabIndex={-1}>
            {editing ? 'Edit scenario' : 'New scenario'}
          </h2>
          <label>
            Name
            <input
              aria-label="Scenario name"
              value={name}
              maxLength={100}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label>
            Description
            <input
              aria-label="Scenario description"
              value={description}
              maxLength={2000}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
          <p>
            Each stage controls a number of read attempts. After the sequence, the final behavior
            repeats until you restart or clear it. Changes require an idle bench.
          </p>
          <div className="scenario-summary">
            <b>{frames.length}</b> {frames.length === 1 ? 'stage' : 'stages'} · <b>{total}</b>{' '}
            staged {total === 1 ? 'read' : 'reads'}
          </div>
          <div className="scenario-stage-controls">
            <span>RESPONSE STAGES</span>
            <button
              className="text-button"
              onClick={() => setExpanded(new Set(frames.map((_, i) => i)))}
            >
              Expand all stages
            </button>
            <button className="text-button" onClick={() => setExpanded(new Set())}>
              Collapse all stages
            </button>
          </div>
          {frames.map((f, i) => (
            <article
              className={`scenario-stage ${expanded.has(i) ? 'expanded' : ''} ${stageErrors[i] ? 'invalid' : ''}`}
              key={i}
            >
              <button
                className="scenario-stage-toggle"
                aria-label={`Edit stage ${i + 1}`}
                aria-expanded={expanded.has(i)}
                onClick={() => toggleStage(i)}
              >
                <span className={`scenario-stage-number ${f.behavior}`}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span>
                  <strong>{behaviors[f.behavior]}</strong>
                  <small>
                    {f.count} read{f.count === 1 ? '' : 's'}
                    {f.behavior === 'delay' ? ` · ${f.delayMs} ms delay` : ''}
                  </small>
                </span>
                <FiChevronDown />
              </button>
              {stageErrors[i] && (
                <p className="scenario-stage-error" role="alert">
                  {stageErrors[i]}
                </p>
              )}
              {expanded.has(i) && (
                <fieldset className="scenario-frame">
                  <legend>Stage {i + 1}</legend>
                  <label>
                    Response
                    <select
                      aria-label={`Stage ${i + 1} response`}
                      value={f.behavior}
                      onChange={(e) =>
                        update(i, {
                          behavior: e.target.value as ScenarioFrame['behavior'],
                          delayMs: 200,
                        })
                      }
                    >
                      {Object.entries(behaviors).map(([id, label]) => (
                        <option key={id} value={id}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="scenario-fields">
                    <label>
                      Read attempts
                      <input
                        aria-label={`Stage ${i + 1} reads`}
                        type="number"
                        min={1}
                        max={100}
                        value={f.count}
                        onChange={(e) => update(i, { count: Number(e.target.value) })}
                      />
                    </label>
                    {f.behavior === 'delay' && (
                      <label>
                        Delay (ms)
                        <input
                          aria-label={`Stage ${i + 1} delay`}
                          type="number"
                          min={0}
                          max={2000}
                          value={f.delayMs ?? 200}
                          onChange={(e) => update(i, { delayMs: Number(e.target.value) })}
                        />
                      </label>
                    )}
                  </div>
                  <div className="scenario-buttons">
                    <button
                      className="text-button"
                      aria-label={`Move stage ${i + 1} up`}
                      disabled={i === 0}
                      onClick={() => {
                        setFrames((previous) => {
                          const next = [...previous];
                          [next[i - 1], next[i]] = [next[i], next[i - 1]];
                          return next;
                        });
                        setExpanded(
                          (previous) =>
                            new Set(
                              [...previous].map((n) => (n === i ? i - 1 : n === i - 1 ? i : n)),
                            ),
                        );
                      }}
                    >
                      Move up
                    </button>
                    <button
                      className="text-button danger"
                      disabled={frames.length === 1}
                      onClick={() => {
                        setFrames((prev) => prev.filter((_, j) => i !== j));
                        setExpanded(
                          (previous) =>
                            new Set(
                              [...previous].filter((n) => n !== i).map((n) => (n > i ? n - 1 : n)),
                            ),
                        );
                      }}
                    >
                      Remove stage {i + 1}
                    </button>
                  </div>
                </fieldset>
              )}
            </article>
          ))}
          {!valid && (
            <p role="alert" className="helper danger">
              Use a name, 1–100 reads per stage, at most 200 staged reads, and delays of 0–2000 ms.
            </p>
          )}
          <div className="scenario-buttons">
            <button
              className="button secondary"
              disabled={frames.length >= 20}
              onClick={() => {
                setExpanded((previous) => new Set([...previous, frames.length]));
                setFrames((prev) => [...prev, { behavior: 'healthy', count: 1 }]);
              }}
            >
              Add stage
            </button>
            <button
              className="button primary"
              disabled={!enabled || !valid}
              onClick={async () => {
                const result = await action(
                  editing ? `/scenarios/${editing.id}` : '/scenarios',
                  editing ? 'PUT' : 'POST',
                  { name, description, frames, version: editing?.version },
                );
                if (result) {
                  setRevealId(result.scenarioId ?? editing?.id ?? '');
                  setRevealVersion((previous) => previous + 1);
                  reset();
                }
              }}
            >
              {editing ? 'Save scenario changes' : 'Save scenario'}
            </button>
            <button className="text-button" onClick={reset}>
              New scenario
            </button>
          </div>
          {error && (
            <p className="helper danger" role="alert">
              {error}
            </p>
          )}
          <label>
            Import scenario JSON
            <input
              aria-label="Import scenario JSON"
              type="file"
              accept=".json,application/json"
              disabled={!enabled}
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                setError('');
                try {
                  if (file.size > 100000) throw new Error('Choose a JSON file under 100 KB.');
                  const result = await action('/scenarios', 'POST', JSON.parse(await file.text()));
                  if (result) {
                    setRevealId(result.scenarioId ?? '');
                    setRevealVersion((previous) => previous + 1);
                    reset();
                  }
                } catch (error) {
                  setError(error instanceof Error ? error.message : 'Invalid scenario JSON.');
                }
                e.target.value = '';
              }}
            />
          </label>
        </section>
        <SavedScenarioLibrary
          lab={lab}
          enabled={enabled}
          revealId={revealId}
          revealVersion={revealVersion}
          onEdit={load}
          onExport={exportScenario}
          onDelete={(s) => {
            if (confirm(`Delete ${s.name}? Applied snapshots remain on their devices.`))
              void action(`/scenarios/${s.id}`, 'DELETE', { version: s.version });
          }}
        />
      </div>
    </>
  );
}
