import { FormEvent, useEffect, useState } from 'react';
import { NavLink, useNavigate, useSearchParams } from 'react-router-dom';
import { SavedPlan, ServerResponse, workspaceRequest } from './backend';
import type { Device } from './simulator';
import './ui-catalog.css';

const route = '/ui-catalogs';

type Location = { path: string; line: number; table: string };
type CatalogItem = { id: string; name: string; pageCount: number; controlCount: number };
type Control = {
  id: string;
  name: string | null;
  pageId: number | string;
  widgetId: number | string;
  buttonType: string | null;
  handler: string | null;
  input: { kind: 'number'; min: number; max: number; step: number } | null;
  source: Location;
  targetPageId?: number;
  targetControlId?: string;
  workflow?: { navigationId: string; confirmationId: string };
  workflowError?: string;
};
type Binding = { handler: string; kind: 'valve' | 'relay'; reference: string };
type CatalogDiff = Record<
  'pages' | 'controls',
  {
    added: { id: string; name: string | null }[];
    removed: { id: string; name: string | null }[];
    changed: { id: string; before: string | null; after: string | null; fields: string[] }[];
    reviewNames: string[];
  }
>;
type Catalog = {
  id: string;
  name: string;
  catalog: {
    pages: { id: string; pageId: number | string; name: string; source: Location }[];
    controls: Control[];
    diagnostics: { code: string; message: string; source: Location }[];
  };
  bindings: Record<string, Binding>;
};

type Props = {
  serverMode: boolean;
  serverReady: boolean;
  canAdmin: boolean;
  canOperate: boolean;
  benchBusy: boolean;
  devices: Device[];
  serverAction: (
    path: string,
    method?: string,
    data?: unknown,
  ) => Promise<ServerResponse | undefined>;
  start: (target: Device, planId: string) => Promise<string | undefined>;
};

export default function UiCatalog({
  serverMode,
  serverReady,
  canAdmin,
  canOperate,
  benchBusy,
  devices,
  serverAction,
  start,
}: Props) {
  const [parameters] = useSearchParams();
  const requestedCatalog = parameters.get('catalog');
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [catalogId, setCatalogId] = useState('');
  const [entry, setEntry] = useState<Catalog>();
  const [pageId, setPageId] = useState('');
  const [controlId, setControlId] = useState('');
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState('');
  const ready = serverMode && serverReady;
  const editable = ready && canAdmin && !benchBusy && !pending;
  const controls =
    entry?.catalog.controls.filter(
      (control) =>
        (!pageId || String(control.pageId) === pageId) &&
        [control.name, control.handler, control.buttonType, control.id].some((value) =>
          value?.toLowerCase().includes(query.trim().toLowerCase()),
        ),
    ) ?? [];
  const selected = controls.find((control) => control.id === controlId) ?? controls[0];

  useEffect(() => {
    if (!ready) return;
    let current = true;
    void workspaceRequest<{ catalogs: CatalogItem[] }>(route)
      .then(({ catalogs }) => {
        if (current) {
          setItems(catalogs);
          setCatalogId(
            (id) =>
              catalogs.find((catalog) => catalog.id === requestedCatalog)?.id ??
              (id || catalogs[0]?.id || ''),
          );
        }
      })
      .catch((error: Error) => {
        if (current) setError(error.message);
      });
    return () => {
      current = false;
    };
  }, [ready, requestedCatalog]);

  useEffect(() => {
    if (!ready || !catalogId) return;
    let current = true;
    void workspaceRequest<{ catalog: Catalog }>(`${route}/${catalogId}`)
      .then(({ catalog }) => {
        if (current) setEntry(catalog);
      })
      .catch((error: Error) => {
        if (current) setError(error.message);
      });
    return () => {
      current = false;
    };
  }, [ready, catalogId]);

  function chooseCatalog(id: string, catalog?: Catalog) {
    setEntry(catalog);
    setCatalogId(id);
    setPageId('');
    setControlId('');
    setQuery('');
    setNotice('');
    setError('');
  }

  async function perform(action: () => Promise<void>) {
    setPending(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'UI catalog request failed.');
    } finally {
      setPending(false);
    }
  }

  function importCatalog(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editable) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    void perform(async () => {
      const files = data.getAll('files').filter((file): file is File => file instanceof File);
      if (!files.length || files.reduce((total, file) => total + file.size, 0) > 512 * 1024) {
        throw new Error('Choose UISee .sql files totaling up to 512 KiB.');
      }
      const names = files.map((file) => file.name.toLowerCase());
      if (new Set(names).size !== files.length)
        throw new Error('Choose files with unique filenames.');
      const sources = await Promise.all(
        files.map(
          async (file) =>
            [
              file.name,
              new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(
                await file.arrayBuffer(),
              ),
            ] as const,
        ),
      );
      const { catalog } = await workspaceRequest<{ catalog: Catalog }>(route, 'POST', {
        name: data.get('name'),
        files: Object.fromEntries(sources),
      });
      setItems((previous) =>
        previous.some((item) => item.id === catalog.id)
          ? previous
          : [
              {
                id: catalog.id,
                name: catalog.name,
                pageCount: catalog.catalog.pages.length,
                controlCount: catalog.catalog.controls.length,
              },
              ...previous,
            ],
      );
      chooseCatalog(catalog.id, catalog);
      setNotice(`${catalog.catalog.controls.length} controls discovered.`);
      form.reset();
    });
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>UISee catalog</h1>
          <p>
            Discover touchscreen controls from UISee SQL files and build tests for reviewed
            handlers.
          </p>
        </div>
      </div>
      {!ready ? (
        <p className="backend-warning">
          <NavLink to="/settings">Connect the Flask workspace</NavLink> to use UISee catalogs.
        </p>
      ) : (
        <div className="ui-catalog">
          {error && (
            <p className="backend-warning" role="alert">
              {error}
            </p>
          )}
          {notice && <p role="status">{notice}</p>}
          {canAdmin && (
            <section className="panel settings-panel">
              <h2>Import UI sources</h2>
              <form onSubmit={importCatalog}>
                <fieldset className="ui-catalog-fields" disabled={!editable}>
                  <label>
                    Catalog name
                    <input name="name" required maxLength={100} />
                  </label>
                  <label>
                    UISee SQL files
                    <input name="files" type="file" accept=".sql" required multiple />
                  </label>
                  <button type="submit" className="button primary">
                    Discover controls
                  </button>
                </fieldset>
              </form>
            </section>
          )}
          <section className="panel settings-panel">
            <h2>Saved controls</h2>
            {items.length === 0 ? (
              <p>No catalogs imported.</p>
            ) : (
              <div className="ui-catalog-fields">
                <label>
                  Catalog
                  <select
                    value={catalogId}
                    disabled={pending}
                    onChange={(event) => chooseCatalog(event.target.value)}
                  >
                    {items.map(({ id, name, controlCount }) => (
                      <option key={id} value={id}>
                        {name} · {controlCount} controls
                      </option>
                    ))}
                  </select>
                </label>
                {entry && (
                  <>
                    <label>
                      Touchscreen page
                      <select value={pageId} onChange={(event) => setPageId(event.target.value)}>
                        <option value="">All pages</option>
                        {entry.catalog.pages.map((page) => (
                          <option value={page.pageId} key={page.id}>
                            {page.name} · {page.pageId}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Search controls
                      <input
                        type="search"
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                      />
                    </label>
                    {controls.length ? (
                      <label>
                        Discovered control
                        <select
                          value={selected?.id ?? ''}
                          onChange={(event) => setControlId(event.target.value)}
                        >
                          {controls.map((control) => (
                            <option value={control.id} key={control.id}>
                              {
                                entry.catalog.pages.find((page) => page.pageId === control.pageId)
                                  ?.name
                              }{' '}
                              / {control.name ?? `Widget ${control.widgetId}`}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : (
                      <p role="status">No controls match.</p>
                    )}
                  </>
                )}
              </div>
            )}
            {entry?.catalog.diagnostics.length ? (
              <details>
                <summary>Discovery messages ({entry.catalog.diagnostics.length})</summary>
                <ul>
                  {entry.catalog.diagnostics.map((item, index) => (
                    <li key={`${item.code}-${index}`}>
                      {item.source.path}:{item.source.line} · {item.message}
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
          </section>
          {entry && items.length > 1 && (
            <CatalogComparison
              key={entry.id}
              current={entry}
              others={items.filter((item) => item.id !== entry.id)}
              perform={perform}
              pending={pending}
            />
          )}
          {entry && selected && (
            <ControlPlan
              key={`${entry.id}:${selected.id}`}
              entry={entry}
              control={selected}
              editable={editable}
              runnable={canOperate && !benchBusy && !pending}
              devices={devices}
              serverAction={serverAction}
              start={start}
              perform={perform}
              onBinding={setEntry}
              onNavigate={(page) => {
                setPageId(String(page));
                setControlId('');
                setQuery('');
              }}
            />
          )}
        </div>
      )}
    </>
  );
}

function CatalogComparison({
  current,
  others,
  perform,
  pending,
}: {
  current: Catalog;
  others: CatalogItem[];
  perform: (action: () => Promise<void>) => Promise<void>;
  pending: boolean;
}) {
  const [baseline, setBaseline] = useState(others[0]?.id ?? '');
  const [diff, setDiff] = useState<CatalogDiff>();
  return (
    <section className="panel settings-panel">
      <h2>Compare releases</h2>
      <div className="ui-catalog-fields">
        <label>
          Baseline catalog
          <select
            value={baseline}
            disabled={pending}
            onChange={(event) => {
              setDiff(undefined);
              setBaseline(event.target.value);
            }}
          >
            {others.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name} · {item.id.slice(0, 8)}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          className="button"
          disabled={!baseline || pending}
          onClick={() =>
            void perform(async () => {
              const { comparison } = await workspaceRequest<{ comparison: CatalogDiff }>(
                `${route}/${current.id}/compare?baseline=${encodeURIComponent(baseline)}`,
              );
              setDiff(comparison);
            })
          }
        >
          Compare with {current.name}
        </button>
      </div>
      {diff &&
        (['pages', 'controls'] as const).map((key) => {
          const group = diff[key];
          return (
            <details open key={key}>
              <summary>
                {key === 'pages' ? 'Pages' : 'Controls'} · {group.added.length} added ·{' '}
                {group.removed.length} removed · {group.changed.length} changed
              </summary>
              <ul>
                {group.added.map((item) => (
                  <li key={`add:${item.id}`}>Added {item.name ?? item.id}</li>
                ))}
                {group.removed.map((item) => (
                  <li key={`remove:${item.id}`}>Removed {item.name ?? item.id}</li>
                ))}
                {group.changed.map((item) => (
                  <li key={`change:${item.id}`}>
                    {item.before !== item.after
                      ? `${item.before ?? item.id} → ${item.after ?? item.id}`
                      : (item.after ?? item.id)}{' '}
                    · {item.fields.join(', ')}
                  </li>
                ))}
                {group.reviewNames.map((name) => (
                  <li key={`review:${name}`}>Review {name}: same name under a different ID.</li>
                ))}
              </ul>
            </details>
          );
        })}
    </section>
  );
}

function ControlPlan({
  entry,
  control,
  editable,
  runnable,
  devices,
  serverAction,
  start,
  perform,
  onBinding,
  onNavigate,
}: {
  entry: Catalog;
  control: Control;
  editable: boolean;
  runnable: boolean;
  devices: Device[];
  serverAction: Props['serverAction'];
  start: Props['start'];
  perform: (action: () => Promise<void>) => Promise<void>;
  onBinding: (catalog: Catalog) => void;
  onNavigate: (pageId: number) => void;
}) {
  const binding = entry.bindings[control.id];
  const output = control.input;
  const title = control.name ?? `Widget ${control.widgetId}`;
  const navigation = entry.catalog.controls.find(
    (node) => node.id === control.workflow?.navigationId,
  );
  const confirmation = entry.catalog.controls.find(
    (node) => node.id === control.workflow?.confirmationId,
  );
  const handlerHint = control.handler ?? confirmation?.handler;
  const targetPage = control.targetPageId;
  const [saved, setSaved] = useState<SavedPlan>();
  const [targetId, setTargetId] = useState('');
  const navigate = useNavigate();
  const compatible = devices.filter((device) => device.connected && device.kind === saved?.kind);
  const target = compatible.find((device) => device.id === targetId) ?? compatible[0];

  function saveBinding(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editable) return;
    const fields = new FormData(event.currentTarget);
    void perform(async () => {
      const { catalog } = await workspaceRequest<{ catalog: Catalog }>(
        `${route}/${entry.id}/bindings`,
        'POST',
        {
          controlId: control.id,
          handler: fields.get('handler'),
          kind: fields.get('kind'),
          reference: fields.get('reference'),
        },
      );
      onBinding(catalog);
    });
  }

  function savePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editable) return;
    const fields = new FormData(event.currentTarget);
    void perform(async () => {
      const result = await serverAction(`${route}/${entry.id}/plans`, 'POST', {
        controlId: control.id,
        name: fields.get('name'),
        value: Number(fields.get('value')),
        expected: Number(fields.get('expected')),
        tolerance: Number(fields.get('tolerance')),
        timeout: 2,
      });
      if (result) setSaved(result.state.testPlans?.find((plan) => plan.id === result.planId));
    });
  }

  return (
    <section className="panel settings-panel">
      <h2>{title}</h2>
      <dl>
        <div>
          <dt>Control ID</dt>
          <dd>{control.id}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>
            <code>
              {control.source.path}:{control.source.line}
            </code>{' '}
            · {control.source.table}
          </dd>
        </div>
        <div>
          <dt>SQL handler hint</dt>
          <dd>{handlerHint ?? 'Unresolved'}</dd>
        </div>
        {navigation && confirmation && (
          <div>
            <dt>Source workflow</dt>
            <dd>
              {navigation.name} → {title} → {confirmation.name}
              <br />
              <code>
                {navigation.source.path}:{navigation.source.line}
              </code>{' '}
              ·{' '}
              <code>
                {control.source.path}:{control.source.line}
              </code>{' '}
              ·{' '}
              <code>
                {confirmation.source.path}:{confirmation.source.line}
              </code>
            </dd>
          </div>
        )}
        {output && (
          <div>
            <dt>Source range</dt>
            <dd>
              {output.min} to {output.max} · step {output.step}
            </dd>
          </div>
        )}
        {binding && (
          <div>
            <dt>Reviewed binding</dt>
            <dd>
              {binding.handler} · {binding.kind} · {binding.reference}
            </dd>
          </div>
        )}
      </dl>
      {targetPage !== undefined && (
        <button className="button" type="button" onClick={() => onNavigate(targetPage)}>
          {title}
        </button>
      )}
      {control.workflowError ? (
        <p role="status">{control.workflowError}</p>
      ) : output ? (
        <>
          <form key={binding?.reference ?? 'new'} onSubmit={saveBinding}>
            <fieldset className="ui-catalog-fields" disabled={!editable}>
              <legend>Review handler binding</legend>
              <label>
                Handler
                <input
                  name="handler"
                  required
                  maxLength={100}
                  defaultValue={handlerHint ?? binding?.handler ?? ''}
                  readOnly={!!handlerHint}
                />
              </label>
              <label>
                Device profile
                <select name="kind" defaultValue={binding?.kind ?? 'valve'}>
                  <option value="valve">Valve</option>
                  <option value="relay">Relay</option>
                </select>
              </label>
              <label>
                Source reference
                <input
                  name="reference"
                  required
                  maxLength={240}
                  defaultValue={binding?.reference ?? ''}
                  placeholder="File and line or approved command specification"
                />
              </label>
              <button className="button" type="submit">
                Save reviewed binding
              </button>
            </fieldset>
          </form>
          {binding && (
            <form onSubmit={savePlan}>
              <fieldset className="ui-catalog-fields" disabled={!editable}>
                <legend>Build verification test</legend>
                <label>
                  Test plan name
                  <input
                    name="name"
                    defaultValue={`${title.slice(0, 80)} readback`}
                    maxLength={100}
                    required
                  />
                </label>
                <label>
                  Command value
                  <input
                    name="value"
                    type="number"
                    min={output.min}
                    max={output.max}
                    step={output.step}
                    required
                  />
                </label>
                <label>
                  Expected device reading
                  <input name="expected" type="number" step="any" required />
                </label>
                <label>
                  Tolerance
                  <input
                    name="tolerance"
                    type="number"
                    min="0"
                    max="1000000"
                    step="any"
                    required
                    defaultValue="0"
                  />
                </label>
                <button className="button primary" type="submit">
                  {confirmation ? 'Save verification test' : 'Confirm and save test'}
                </button>
              </fieldset>
            </form>
          )}
        </>
      ) : (
        targetPage === undefined &&
        !control.targetControlId && (
          <p>Test generation requires a numeric control with source-declared bounds.</p>
        )
      )}
      {saved && (
        <div className="ui-catalog-fields">
          <p role="status">
            Saved {saved.name}. <NavLink to="/plans">Open the plan library</NavLink> to export or
            replay it.
          </p>
          {target ? (
            <>
              <label>
                Connected target
                <select value={target.id} onChange={(event) => setTargetId(event.target.value)}>
                  {compatible.map((device) => (
                    <option value={device.id} key={device.id}>
                      {device.name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="button primary"
                disabled={!runnable}
                type="button"
                onClick={() =>
                  void perform(async () => {
                    if (await start(target, saved.id)) navigate('/results');
                  })
                }
              >
                Run saved test
              </button>
            </>
          ) : (
            <p>
              <NavLink to="/devices">Connect a compatible device</NavLink> to run this plan.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
