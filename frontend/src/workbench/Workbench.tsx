import { useEffect, useRef, useState } from 'react';
import { NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { FiActivity, FiArrowUpRight, FiBox, FiCheck, FiChevronRight, FiCpu, FiDownload, FiGrid, FiLink, FiPlay, FiPlus, FiRadio, FiRefreshCw, FiSearch, FiSquare, FiTerminal, FiTrash2, FiX } from 'react-icons/fi';
import { controlValue, createDevice, createRun, Device, DeviceKind, evaluateStep, Fault, finishRun, initialState, LabState, loadState, logEntry, Plan, planNames, profiles, saveState, telemetry, TestRun } from './simulator';
import './workbench.css';
import BlueprintLibrary from './BlueprintLibrary';
import TestPlanLibrary from './TestPlanLibrary';
import { labRequest, savedBackendMode, ServerResponse } from './backend';

function download(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const clock = (time: string) => new Date(time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
const reading = (device: Device) => device.kind === 'relay' ? (device.value ? 'ON' : 'OFF') : `${device.value}${profiles[device.kind].unit}`;
function Status({ value }: { value: string }) { return <span className={`status status-${value.toLowerCase()}`}><i />{value}</span>; }

export default function Workbench() {
  const [lab, setLab] = useState<LabState>(() => savedBackendMode() ? { version: 1, devices: [], runs: [], logs: [] } : loadState());
  const [serverMode, setServerMode] = useState(savedBackendMode);
  const serverRef = useRef(serverMode); serverRef.current = serverMode;
  const [serverError, setServerError] = useState('');
  const [serverReady, setServerReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const revisionRef = useRef(-1);
  const [hardwareAllowed, setHardwareAllowed] = useState(false);
  const [apiToken, setApiToken] = useState(() => sessionStorage.getItem('hardware-tester.api-token') ?? '');
  const [adapter, setAdapter] = useState<'simulation' | 'serial' | 'mqtt'>('simulation');
  const [endpoint, setEndpoint] = useState('');
  const [selected, setSelected] = useState(() => lab.devices[0]?.id ?? '');
  const [notice, setNotice] = useState('');
  const [storageError, setStorageError] = useState(false);
  const [modal, setModal] = useState(false);
  const [name, setName] = useState('');
  const [kind, setKind] = useState<DeviceKind>('temperature');
  const [plan, setPlan] = useState<string>('smoke');
  const [query, setQuery] = useState('');
  const [logFilter, setLogFilter] = useState('all');
  const [viewRun, setViewRun] = useState('');
  const labRef = useRef(lab); labRef.current = lab;
  const activeRef = useRef<{ id: string; index: number; original: Device } | null>(null);
  const tickRef = useRef(0);
  const device = lab.devices.find(d => d.id === selected);
  const activeRun = lab.runs.find(r => r.status === 'running');
  const connected = lab.devices.filter(d => d.connected).length;
  const finished = lab.runs.filter(r => r.status === 'passed' || r.status === 'failed');
  const passed = finished.filter(r => r.status === 'passed').length;
  const currentRun = lab.runs.find(r => r.id === viewRun) ?? lab.runs[0];
  useEffect(() => {
    if (plan !== 'smoke' && plan !== 'control' && (!serverMode || !lab.testPlans?.some(p => p.id === plan && p.kind === device?.kind))) setPlan('smoke');
  }, [plan, serverMode, lab.testPlans, device?.kind]);

  const update = (fn: (state: LabState) => LabState) => setLab(previous => {
    const next = fn(previous); labRef.current = next; return next;
  });
  const announce = (message: string) => setNotice(message);
  const record = (state: LabState, message: string, level: 'info' | 'error' | 'success' = 'info') => ({ ...state, logs: [logEntry(message, level), ...state.logs].slice(0, 250) });

  function acceptServer(result: ServerResponse) {
    if ((result.state.revision ?? 0) < revisionRef.current) return;
    revisionRef.current = result.state.revision ?? 0;
    setLab(result.state); labRef.current = result.state;
    setSelected(previous => result.state.devices.some(d => d.id === previous) ? previous : result.state.devices[0]?.id ?? '');
    if (result.capabilities) setHardwareAllowed(result.capabilities.hardware);
    setServerReady(true); setServerError('');
  }
  async function serverAction(path: string, method = 'POST', data: unknown = {}) {
    if (busyRef.current) return;
    busyRef.current = true; setBusy(true);
    try { const result = await labRequest(path, method, data); acceptServer(result); return result; }
    catch (error) { setNotice(error instanceof Error ? error.message : 'Backend request failed.'); }
    finally { busyRef.current = false; setBusy(false); }
  }
  async function chooseEngine(useServer: boolean) {
    if (activeRun || busyRef.current) return;
    if (useServer) {
      revisionRef.current = -1;
      try { const result = await labRequest(); acceptServer(result); }
      catch (error) { setNotice(`Could not switch to Flask: ${error instanceof Error ? error.message : 'Backend unavailable.'}`); return; }
    } else { const next = loadState(); setLab(next); setSelected(next.devices[0]?.id ?? ''); setServerReady(false); }
    setViewRun(''); setServerMode(useServer); serverRef.current = useServer;
    setServerError(''); setStorageError(false);
    try { localStorage.setItem('hardware-tester.engine', useServer ? 'server' : 'browser'); } catch { /* Engine still works without storage. */ }
  }
  useEffect(() => {
    if (!serverMode) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try { const result = await labRequest(); if (!stopped) acceptServer(result); }
      catch (error) { if (!stopped) { setServerReady(false); setServerError(error instanceof Error ? error.message : 'Backend unavailable.'); } }
      if (!stopped) timer = setTimeout(poll, 1000);
    }
    poll(); return () => { stopped = true; clearTimeout(timer); };
  }, [serverMode]);
  useEffect(() => { if (!serverMode) setStorageError(!saveState(lab)); }, [lab, serverMode]);
  useEffect(() => {
    if (!notice) return;
    const timeout = setTimeout(() => setNotice(''), 5000); return () => clearTimeout(timeout);
  }, [notice]);
  useEffect(() => {
    const timer = setInterval(() => {
      if (serverRef.current) return;
      tickRef.current++;
      setLab(previous => {
        const next = { ...previous, devices: previous.devices.map(d => d.connected && d.fault !== 'timeout' && !(activeRef.current?.original.id === d.id && activeRef.current.index > 1) ? { ...d, value: telemetry(d, tickRef.current) } : d) };
        labRef.current = next; return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    const timer = setInterval(() => {
      if (serverRef.current) return;
      const active = activeRef.current;
      if (!active) return;
      const state = labRef.current;
      const run = state.runs.find(r => r.id === active.id);
      if (!run || run.status !== 'running') { activeRef.current = null; return; }
      let target = state.devices.find(d => d.id === run.deviceId);
      const stepName = run.steps[active.index].name;
      const isCommand = stepName === 'Send control command';
      const isRestore = stepName === 'Restore initial state';
      if (target && target.connected && target.fault !== 'timeout' && (isCommand || isRestore)) {
        target = { ...target, value: isRestore ? active.original.value : target.fault === 'out-of-range' ? telemetry(target, 0) : controlValue(target), enabled: isRestore ? active.original.enabled : true };
      }
      if (target && target.fault === 'out-of-range') target = { ...target, value: telemetry(target, 0) };
      const result = evaluateStep(target, stepName);
      let nextRun: TestRun = { ...run, steps: run.steps.map((s, i) => i === active.index ? result : s) };
      // A control response must match the command, as well as satisfy its operating range.
      if (stepName === 'Verify response' && result.status === 'passed' && target && target.value !== controlValue(target)) {
        nextRun.steps[active.index] = { ...result, status: 'failed', detail: `Expected ${controlValue(target)}, received ${target.value}.` };
      }
      active.index++;
      const done = active.index === run.steps.length;
      if (done) {
        nextRun = finishRun(nextRun); activeRef.current = null;
        if (target && run.plan === planNames.control) target = { ...target, value: active.original.value, enabled: active.original.enabled };
      }
      const resolvedTarget = target;
      update(previous => record({ ...previous, devices: previous.devices.map(d => d.id === run.deviceId && resolvedTarget ? resolvedTarget : d), runs: previous.runs.map(r => r.id === run.id ? nextRun : r) }, `${run.deviceName} · ${stepName}: ${nextRun.steps[active.index - 1].detail}`, nextRun.steps[active.index - 1].status === 'failed' ? 'error' : 'success'));
      if (done) announce(`${run.deviceName}: ${nextRun.status}.`);
    }, 750);
    return () => clearInterval(timer);
  }, []);

  function connect(id: string) {
    if (serverMode) { void serverAction(`/devices/${id}/connection`, 'POST', { connected: !lab.devices.find(d => d.id === id)?.connected }); return; }
    update(state => {
      const target = state.devices.find(d => d.id === id)!;
      const next = !target.connected;
      return record({ ...state, devices: state.devices.map(d => d.id === id ? { ...d, connected: next } : d) }, `${target.name} ${next ? 'connected to' : 'disconnected from'} ${target.endpoint}.`, next ? 'success' : 'info');
    });
  }
  function connectAll() {
    if (serverMode) { void serverAction('/connect-bench'); return; }
    update(state => record({ ...state, devices: state.devices.map(d => ({ ...d, connected: true })) }, `Connected ${state.devices.length} virtual devices.`, 'success'));
    announce('Simulation bench connected. Select a device to run a test.');
  }
  function setFault(fault: Fault) {
    if (!device) return;
    if (serverMode) { void serverAction(`/devices/${selected}/fault`, 'POST', { fault }); return; }
    update(state => record({ ...state, devices: state.devices.map(d => d.id === selected ? { ...d, fault, value: fault === 'out-of-range' ? telemetry({ ...d, fault }, 0) : fault === 'none' ? d.kind === 'temperature' ? 24 : 0 : d.value } : d) }, `${device.name}: ${fault === 'none' ? 'fault cleared' : `injected ${fault} fault`}.`, fault === 'none' ? 'info' : 'error'));
  }
  function command(value: number) {
    if (!device?.connected || activeRun) return;
    if (serverMode) { void serverAction(`/devices/${selected}/command`, 'POST', { value }); return; }
    if (device.fault === 'timeout') { update(s => record(s, `${device.name}: command timed out.`, 'error')); announce('Command timed out. Clear the injected fault to retry.'); return; }
    update(state => record({ ...state, devices: state.devices.map(d => d.id === selected ? { ...d, value: d.fault === 'out-of-range' ? telemetry(d, 0) : value, enabled: value > 0 } : d) }, `${device.name}: sent ${value}${profiles[device.kind].unit} command.`, 'success'));
  }
  function start() {
    if (!device?.connected || activeRef.current) return;
    if (serverMode) { void serverAction('/runs', 'POST', { deviceId: selected, plan }).then(r => { if (r?.runId) setViewRun(r.runId); }); return; }
    const run = createRun(device, plan as Plan);
    activeRef.current = { id: run.id, index: 0, original: { ...device } };
    setViewRun(run.id);
    update(state => record({ ...state, runs: [run, ...state.runs].slice(0, 100) }, `Started ${run.plan} on ${device.name}.`));
  }
  function cancel() {
    if (serverMode) { void serverAction('/runs/cancel'); return; }
    const active = activeRef.current; if (!active) return;
    activeRef.current = null;
    update(state => record({ ...state, devices: state.devices.map(d => d.id === active.original.id ? { ...d, value: active.original.value, enabled: active.original.enabled } : d), runs: state.runs.map(r => r.id === active.id ? finishRun(r, true) : r) }, 'Run cancelled. Original control state restored.'));
    announce('Test cancelled.');
  }
  async function addDevice(event: React.FormEvent) {
    event.preventDefault(); if (!name.trim() || lab.devices.length >= 100) return;
    if (serverMode) {
      const result = await serverAction('/devices', 'POST', { kind, name: name.trim(), adapter, endpoint });
      if (result?.deviceId) { setSelected(result.deviceId); setModal(false); setName(''); setEndpoint(''); }
      return;
    }
    const next = createDevice(kind, name.trim()); update(state => record({ ...state, devices: [...state.devices, next] }, `Added ${next.name} (${next.protocol} simulator).`));
    setSelected(next.id); setModal(false); setName(''); announce(`${next.name} added. Connect it to begin.`);
  }
  function removeDevice() {
    if (!device || activeRun) return;
    if (serverMode) { void serverAction(`/devices/${selected}`, 'DELETE'); return; }
    const remaining = lab.devices.filter(d => d.id !== selected);
    update(state => record({ ...state, devices: remaining }, `Removed ${device.name}.`)); setSelected(remaining[0]?.id ?? '');
  }
  const deviceCards = (filter = false) => <div className="device-grid">{lab.devices.filter(d => !filter || d.name.toLowerCase().includes(query.toLowerCase()) || d.protocol.toLowerCase().includes(query.toLowerCase())).map(d => <button className={`device-card ${selected === d.id ? 'selected' : ''}`} key={d.id} onClick={() => setSelected(d.id)}>
    <div className="device-card-top"><span className={`device-icon ${d.kind}`}><FiCpu /></span><Status value={d.connected ? d.lastError ? 'fault' : d.fault === 'none' ? 'connected' : 'fault' : 'offline'} /></div>
    <strong>{d.name}</strong><span className="muted">{profiles[d.kind].name}</span><div className="device-reading">{d.connected ? d.lastError || d.fault === 'timeout' ? '—' : reading(d) : '—'}<span>{d.protocol}<FiChevronRight /></span></div>
  </button>)}{!lab.devices.length && <div className="empty">Your bench is empty. Add a virtual device to start.</div>}{filter && lab.devices.length > 0 && !lab.devices.some(d => d.name.toLowerCase().includes(query.toLowerCase()) || d.protocol.toLowerCase().includes(query.toLowerCase())) && <div className="empty">No devices match your search.</div>}</div>;
  const inspector = <section className="panel inspector"><div className="panel-heading"><div><span className="eyebrow">DEVICE INSPECTOR</span><h2>{device?.name ?? 'Select a device'}</h2></div><FiCpu /></div>{device ? <>
    <div className="inspect-reading"><span>{device.connected && !device.lastError && device.fault !== 'timeout' ? reading(device) : '—'}</span><Status value={device.connected ? device.lastError ? 'fault' : device.fault === 'none' ? 'connected' : 'fault' : 'offline'} /></div>
    <dl><div><dt>Transport</dt><dd>{device.protocol} · {device.adapter && device.adapter !== 'simulation' ? 'hardware' : 'emulated'}</dd></div><div><dt>Endpoint</dt><dd className="mono">{device.endpoint}</dd></div><div><dt>Update interval</dt><dd>1,000 ms</dd></div></dl>
    <button disabled={busy || (serverMode && !serverReady)} className={`button ${device.connected ? 'secondary' : 'primary'} full`} onClick={() => connect(device.id)}><FiLink />{device.connected ? 'Disconnect device' : 'Connect device'}</button>
    {(device.safetyWarning || device.lastError) && <p className="helper danger" style={{padding: 19}} role="alert">{device.safetyWarning || device.lastError}</p>}<div className="inspector-section"><label htmlFor="fault">Fault injection</label><select id="fault" disabled={busy || (device.adapter !== undefined && device.adapter !== 'simulation')} value={device.fault} onChange={e => setFault(e.target.value as Fault)}><option value="none">Healthy · no fault</option><option value="timeout">Transport timeout</option><option value="out-of-range">Out-of-range reading</option></select><p className="helper">Introduce a failure to verify that your tests catch it.</p></div>
    {device.kind !== 'temperature' && <div className="inspector-section"><label>{device.kind === 'valve' ? 'Valve position' : 'Relay output'}</label>{device.kind === 'valve' ? <input aria-label="Valve position" type="range" min="0" max="100" value={Math.min(device.value, 100)} disabled={!device.connected || !!activeRun || busy || (serverMode && !serverReady)} onChange={e => command(Number(e.target.value))} /> : <button className="button secondary full" disabled={!device.connected || !!activeRun || busy || (serverMode && !serverReady)} onClick={() => command(device.value ? 0 : 1)}>{device.value ? 'Switch OFF' : 'Switch ON'}</button>}</div>}
    <button className="text-button danger" disabled={!!activeRun || busy} onClick={removeDevice}><FiTrash2 /> Remove device</button>
  </> : <p className="empty">Choose a device from your bench to view telemetry and controls.</p>}</section>;
  const runner = <section className="panel runner"><div className="panel-heading"><div><span className="eyebrow">TEST RUNNER</span><h2>Validate your connection</h2></div><span className="subtle-label">{activeRun ? 'RUNNING' : 'READY'}</span></div>
    <div className="run-controls"><label>Target device<select value={selected} disabled={!!activeRun} onChange={e => setSelected(e.target.value)}>{!lab.devices.length && <option value="">No devices available</option>}{lab.devices.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select></label><label>Test plan<select aria-label="Test plan" value={plan} disabled={!!activeRun} onChange={e => setPlan(e.target.value)}>{Object.entries(planNames).map(([id, label]) => <option key={id} value={id}>{label}</option>)}{serverMode && lab.testPlans?.filter(p => p.kind === device?.kind).map(p => <option key={p.id} value={p.id}>{p.name} · v{p.version}</option>)}</select></label><button className={`button ${activeRun ? 'secondary' : 'primary'}`} disabled={busy || (serverMode && !serverReady) || (!activeRun && !device?.connected)} onClick={activeRun ? cancel : start}>{activeRun ? <FiSquare /> : <FiPlay />}{activeRun ? 'Stop test' : 'Run test'}</button></div>
    {!device?.connected && !activeRun && <p className="helper">Connect the selected device before running a test.</p>}
    {currentRun ? <div className="steps"><div className="result-heading"><strong>{currentRun.plan} <span className="muted">/ {currentRun.deviceName}</span></strong><Status value={currentRun.status} /></div>{currentRun.steps.map((step, i) => <div className={`step step-${step.status}`} key={i}><span className="step-icon">{step.status === 'passed' ? <FiCheck /> : step.status === 'failed' ? <FiX /> : i + 1}</span><div><strong>{step.name}</strong><p>{step.detail}</p></div><span className="step-state">{step.status}</span></div>)}</div> : <div className="runner-empty"><span><FiActivity /></span><strong>Your first test starts here</strong><p>Check the handshake, read telemetry, and validate<br />the operating range of a virtual device.</p></div>}
  </section>;
  const logPanel = (full = false) => <section className="panel log-panel"><div className="panel-heading"><div><span className="eyebrow">EVENT STREAM</span><h2>Activity log</h2></div><div className="inline"><select aria-label="Filter logs" value={logFilter} onChange={e => setLogFilter(e.target.value)}><option value="all">All events</option><option value="error">Errors</option><option value="success">Successes</option><option value="info">Info</option></select><button className="icon-button" aria-label="Export logs" onClick={() => download('hardware-tester-logs.json', lab.logs)}><FiDownload /></button></div></div><div className={`log-stream ${full ? 'tall' : ''}`}>{lab.logs.filter(l => logFilter === 'all' || l.level === logFilter).slice(0, full ? 250 : 12).map(l => <div className="log-line" key={l.id}><time>{clock(l.time)}</time><span className={`log-level ${l.level}`}>{l.level}</span><span>{l.message}</span></div>)}{!lab.logs.filter(l => logFilter === 'all' || l.level === logFilter).length && <p className="empty">{lab.logs.length ? 'No events match this filter.' : 'Waiting for activity. Connect a device to begin.'}</p>}</div></section>;
  const history = <section className="panel"><div className="panel-heading"><div><span className="eyebrow">RUN HISTORY</span><h2>Results you can inspect</h2></div><button className="button secondary" disabled={!lab.runs.length || !!activeRun} onClick={() => download('hardware-tester-results.json', { version: 1, mode: serverMode ? 'server' : 'simulation', exportedAt: new Date().toISOString(), runs: lab.runs })}><FiDownload /> Export results</button></div><div className="table-wrap"><table><thead><tr><th>Device / plan</th><th>Started</th><th>Checks passed</th><th>Result</th><th /></tr></thead><tbody>{lab.runs.map(r => <tr key={r.id}><td><strong>{r.deviceName}</strong><span className="table-sub">{r.plan}</span></td><td>{new Date(r.startedAt).toLocaleString()}</td><td>{r.steps.filter(s => s.status === 'passed').length} / {r.steps.length}</td><td><Status value={r.status} /></td><td><button className="text-button" onClick={() => setViewRun(r.id)}>Inspect <FiArrowUpRight /></button></td></tr>)}</tbody></table>{!lab.runs.length && <p className="empty">No results yet. Run a test to build your history.</p>}</div></section>;

  return <div className="workbench"><aside className="lab-sidebar"><NavLink to="/overview" className="brand"><span><FiCpu /></span><div>Hardware<span>TESTER / LAB</span></div></NavLink><div className="sidebar-label">WORKSPACE</div><nav>{[[ '/overview', 'Overview', FiGrid ], ['/devices', 'Devices', FiCpu], ['/blueprints', 'Blueprints', FiBox], ['/plans', 'Plan library', FiCheck], ['/tests', 'Test bench', FiPlay], ['/results', 'Results', FiActivity], ['/logs', 'Activity log', FiTerminal]].map(([to, label, Icon]) => { const Component = Icon as typeof FiGrid; return <NavLink key={String(to)} to={String(to)} aria-label={String(label)}><Component /><span>{String(label)}</span>{to === '/devices' && <small>{lab.devices.length}</small>}</NavLink>; })}</nav><div className="sidebar-bottom"><div className="simulation-note"><FiRadio /><strong>{serverMode ? 'Connected workspace' : 'Simulation workspace'}</strong><p>{serverMode ? 'Server-managed devices and test flows.' : <>Virtual devices. Real test flows.<br />No physical hardware required.</>}</p><span><i />{serverMode ? serverReady ? 'Flask engine connected' : 'Flask unavailable' : 'Local engine available'}</span></div><NavLink to="/settings" aria-label="Workspace settings" className="sidebar-settings"><FiBox /><span>Workspace settings</span></NavLink></div></aside>
    <div className="lab-main"><header className="lab-topbar"><div><span className="breadcrumb">Workspace</span><FiChevronRight /><strong>Development lab</strong></div><div className="inline"><span className="mode-pill"><FiRadio /> {serverMode ? lab.devices.some(d => d.adapter && d.adapter !== 'simulation') ? 'HARDWARE LAB' : 'SERVER SIMULATION' : 'SIMULATION'}</span><span className="avatar">HT</span></div></header>
      <main className="lab-content">{serverError && <div className="backend-warning" role="alert">Backend unavailable: {serverError} Commands are disabled until reconnection.</div>}{busy && <div className="backend-busy" role="status">Waiting for backend acknowledgement…</div>}<Routes><Route path="/" element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<><div className="page-heading"><div><span className="eyebrow">YOUR HARDWARE, UNDER CONTROL</span><h1>Good things start on the bench.</h1><p>Connect, experiment, and validate. All in one workspace.</p></div><button className="button primary" disabled={lab.devices.length >= 100} onClick={() => setModal(true)}><FiPlus /> Add device</button></div>
          <div className="stats"><div><span><FiCpu /> Devices on bench</span><strong>{lab.devices.length}<small>virtual devices</small></strong></div><div><span><FiLink /> Active connections</span><strong>{connected}<small>of {lab.devices.length} connected</small></strong></div><div><span><FiCheck /> Test pass rate</span><strong>{finished.length ? `${Math.round(passed / finished.length * 100)}%` : '—'}<small>{finished.length ? `${passed} of ${finished.length} completed runs` : 'Run your first test'}</small></strong></div><div><span><FiActivity /> Tests executed</span><strong>{lab.runs.length}<small>{activeRun ? '1 test in progress' : 'Ready for the next run'}</small></strong></div></div>
          <div className="bench-banner"><span className="banner-icon"><FiRadio /></span><div><strong>A complete lab. Without the cables.</strong><p>Your MQTT sensor, serial valve, and USB relay are ready to emulate.</p></div><button className="button secondary" disabled={busy || (serverMode && !serverReady) || !lab.devices.length || connected === lab.devices.length} onClick={connectAll}>{connected === lab.devices.length && lab.devices.length ? <><FiCheck /> Bench connected</> : <><FiLink /> Connect bench</>}</button></div>
          <div className="workspace-grid"><div><div className="section-heading"><h2>Device bench <span>{lab.devices.length}</span></h2><NavLink to="/devices">Manage devices <FiArrowUpRight /></NavLink></div>{deviceCards()}{runner}</div>{inspector}</div>{logPanel()}</>} />
        <Route path="/devices" element={<><div className="page-heading"><div><span className="eyebrow">VIRTUAL HARDWARE</span><h1>Device bench</h1><p>Explore simulated transports and control device behavior.</p></div><button className="button primary" disabled={lab.devices.length >= 100} onClick={() => setModal(true)}><FiPlus /> Add device</button></div><div className="toolbar"><label className="search"><FiSearch /><input aria-label="Search devices" placeholder="Search by name or transport…" value={query} onChange={e => setQuery(e.target.value)} /></label><button className="button secondary" disabled={busy || (serverMode && !serverReady) || !lab.devices.length} onClick={connectAll}><FiLink /> Connect all</button></div><div className="workspace-grid"><div>{deviceCards(true)}</div>{inspector}</div></>} />
        <Route path="/tests" element={<><div className="page-heading"><div><span className="eyebrow">EXECUTE & OBSERVE</span><h1>Test bench</h1><p>Run reproducible checks. Inject a fault to watch them fail.</p></div></div><div className="workspace-grid"><div>{runner}{logPanel()}</div>{inspector}</div></>} />
        <Route path="/results" element={<><div className="page-heading"><div><span className="eyebrow">VALIDATION RECORD</span><h1>Test results</h1><p>Inspect every check and export a portable JSON report.</p></div></div>{history}{currentRun && runner}{currentRun?.configuration && <section className="panel settings-panel" style={{marginTop:24}}><h2>Configuration used for this run</h2><p>{currentRun.configuration.plan.name} · version {currentRun.configuration.plan.version} · {currentRun.configuration.device.adapter || 'simulation'} · {currentRun.configuration.device.endpoint}</p><details><summary>View saved plan and device settings</summary><pre className="run-configuration">{JSON.stringify(currentRun.configuration, null, 2)}</pre></details><button className="button secondary" onClick={() => download('hardware-tester-run.json', currentRun)}>Export this run</button></section>}</>} />
        <Route path="/plans" element={<TestPlanLibrary lab={lab} enabled={serverMode && serverReady && !busy && !activeRun} action={serverAction} />} /><Route path="/blueprints" element={<BlueprintLibrary lab={lab} enabled={serverMode && serverReady && !busy && !activeRun} action={serverAction} />} /><Route path="/logs" element={<><div className="page-heading"><div><span className="eyebrow">TRANSPORT & TEST EVENTS</span><h1>Activity log</h1><p>The latest 250 events from your simulation workspace.</p></div></div>{logPanel(true)}</>} />
        <Route path="/settings" element={<><div className="page-heading"><div><span className="eyebrow">WORKSPACE</span><h1>Lab settings</h1><p>A self-contained environment for developing your hardware test flows.</p></div></div><section className="panel settings-panel"><h2>Execution engine</h2><p>Browser mode keeps a private local bench. Flask mode uses shared SQLite state and continues tests when you close or reload a tab. Each workspace is separate.</p><label>Backend API token (optional)<input type="password" value={apiToken} onChange={e => { setApiToken(e.target.value); sessionStorage.setItem('hardware-tester.api-token', e.target.value); }} autoComplete="off" /></label><div className="inline" style={{marginTop: 16}}><button className="button secondary" disabled={serverMode || !!activeRun || busy} onClick={() => chooseEngine(true)}>Connect Flask backend</button><button className="button secondary" disabled={!serverMode || !!activeRun || busy} onClick={() => chooseEngine(false)}>Use browser simulator</button><Status value={serverMode ? serverReady ? 'connected' : 'offline' : 'offline'} /></div><h2>Simulation engine</h2><p>Simulated MQTT, Serial, and USB devices run in the selected engine. Real serial and MQTT adapters are available in Flask mode when the backend explicitly enables hardware.</p><dl><div><dt>Persistence</dt><dd>{serverMode ? 'Device configurations, runs, and logs are stored in SQLite on the server.' : 'Device configurations and the last 100 test runs stay in this browser.'}</dd></div><div><dt>Reconnect behavior</dt><dd>{serverMode ? 'Tests survive tab reloads. Server restarts cancel interrupted tests and disconnect transports.' : 'Devices disconnect on reload; interrupted tests are marked cancelled.'}</dd></div><div><dt>Fault profiles</dt><dd>Transport timeout and out-of-range telemetry.</dd></div></dl><h2>Workspace data</h2><p>Export your complete bench before resetting. Reset removes devices, peripherals, history, and logs. Saved server blueprints and test plans remain in their libraries.</p><div className="inline"><button className="button secondary" onClick={() => download('hardware-tester-workspace.json', lab)}><FiDownload /> Export workspace</button><button className="button secondary danger" disabled={!!activeRun} onClick={() => { if (window.confirm('Reset the selected workspace? This removes devices, test history, and logs for this workspace.')) { if (serverMode) { void serverAction('/reset'); return; } const next = initialState(); update(() => next); setSelected(next.devices[0].id); setViewRun(''); announce('Workspace reset.'); } }}><FiRefreshCw /> Reset workspace</button></div><h2>Existing dashboards</h2><p>The original dashboards are retained for reference. Their older API contract is separate from this workbench backend and still needs migration.</p><a className="text-button" href="/legacy/emulator">Open original dashboards <FiArrowUpRight /></a></section></>} />
        <Route path="*" element={<div className="empty"><h1>Page not found</h1><NavLink to="/overview">Return to the workbench</NavLink></div>} />
      </Routes><footer className="lab-footer"><span>HARDWARE TESTER <b>/</b> Development workspace</span><span><i /> {lab.devices.some(d => d.adapter && d.adapter !== 'simulation') ? 'Real hardware adapters configured' : 'All connections are simulated'}</span></footer></main>
    </div>
    {storageError && <div className="storage-warning" role="alert">Browser storage is unavailable. Export results before closing this page.</div>}
    {notice && <div className="lab-toast" role="status"><FiCheck />{notice}<button aria-label="Dismiss notification" onClick={() => setNotice('')}><FiX /></button></div>}
    {modal && <div className="modal-backdrop" onClick={() => setModal(false)}><section className="lab-modal" role="dialog" aria-modal="true" aria-labelledby="add-title" onClick={e => e.stopPropagation()} onKeyDown={e => { if (e.key === 'Escape') setModal(false); if (e.key === 'Tab') { const items = Array.from(e.currentTarget.querySelectorAll<HTMLElement>('button,input,select')); const first = items[0], last = items[items.length - 1]; if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); } } }}><div className="panel-heading"><div><span className="eyebrow">EXPAND YOUR BENCH</span><h2 id="add-title">{serverMode ? 'Add a device' : 'Add a virtual device'}</h2></div><button className="icon-button" aria-label="Close dialog" onClick={() => setModal(false)}><FiX /></button></div><form onSubmit={addDevice}><label>Device name<input autoFocus required maxLength={100} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Outlet temperature" /></label>{serverMode && <><label>Transport adapter<select value={adapter} onChange={e => setAdapter(e.target.value as typeof adapter)}><option value="simulation">Simulation · no physical hardware</option><option value="serial" disabled={!hardwareAllowed}>Real serial · JSON protocol</option><option value="mqtt" disabled={!hardwareAllowed}>Real MQTT · JSON protocol</option></select></label>{adapter !== 'simulation' && <label>Connection endpoint<input required value={endpoint} onChange={e => setEndpoint(e.target.value)} placeholder={adapter === 'serial' ? 'COM3 or /dev/ttyUSB0' : 'mqtt://localhost:1883/lab/device'} /><p className="helper">Connect only devices implementing the documented Hardware Tester JSON command protocol. Real commands can change outputs.</p></label>}</>}<label>Hardware profile<select value={kind} onChange={e => setKind(e.target.value as DeviceKind)}>{Object.entries(profiles).map(([id, p]) => <option key={id} value={id}>{p.name} · {p.protocol}</option>)}</select></label><div className="profile-preview"><FiCpu /><div><strong>{profiles[kind].protocol} simulator</strong><p className="mono">{profiles[kind].endpoint}</p></div></div><button className="button primary full" disabled={!name.trim() || busy || (serverMode && adapter !== 'simulation' && !endpoint.trim())}><FiPlus /> Add to bench</button></form></section></div>}
  </div>;
}
