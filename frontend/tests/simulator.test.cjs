const { test } = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const fs = require('node:fs');
const Module = require('node:module');
const path = require('node:path');
const filename = path.resolve(__dirname, '../src/workbench/simulator.ts');
const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
});
const loaded = new Module(filename, module);
loaded._compile(compiled.outputText, filename);
const sim = loaded.exports;
const store = new Map();
global.localStorage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, v) };
test('all profiles pass health checks when connected', () => {
  for (const kind of Object.keys(sim.profiles)) {
    const device = { ...sim.createDevice(kind), connected: true };
    const run = sim.createRun(device, 'smoke');
    run.steps = run.steps.map((step) => sim.evaluateStep(device, step.name));
    assert.equal(sim.finishRun(run).status, 'passed');
  }
});
test('transport timeout fails a check rather than producing a success', () => {
  const device = { ...sim.createDevice('temperature'), connected: true, fault: 'timeout' };
  assert.equal(sim.evaluateStep(device, 'Read telemetry').status, 'failed');
});
test('out-of-range telemetry fails validation for every profile', () => {
  for (const kind of Object.keys(sim.profiles)) {
    const device = { ...sim.createDevice(kind), connected: true, fault: 'out-of-range' };
    device.value = sim.telemetry(device, 1);
    assert.equal(sim.evaluateStep(device, 'Validate operating range').status, 'failed');
  }
});
test('disconnected and missing targets fail cleanly', () => {
  assert.equal(
    sim.evaluateStep(sim.createDevice('valve'), 'Connection handshake').status,
    'failed',
  );
  assert.equal(sim.evaluateStep(undefined, 'Read telemetry').status, 'failed');
});
test('control plans include verification and restoration', () => {
  const d = sim.createDevice('valve');
  const run = sim.createRun(d, 'control');
  assert.deepEqual(
    run.steps.map((s) => s.name),
    ['Connection handshake', 'Send control command', 'Verify response', 'Restore initial state'],
  );
  assert.equal(sim.controlValue(d), 75);
  assert.equal(sim.controlValue(sim.createDevice('relay')), 1);
  assert.equal(sim.controlValue(sim.createDevice('temperature')), 30);
});
test('failed checks propagate to run results; cancelled runs stay cancelled', () => {
  const run = sim.createRun(sim.createDevice('relay'), 'smoke');
  run.steps[0] = sim.evaluateStep(undefined, run.steps[0].name);
  assert.equal(sim.finishRun(run).status, 'failed');
  assert.equal(sim.finishRun(run, true).status, 'cancelled');
});
test('reload disconnects targets, cancels interrupted runs, and restores controls', () => {
  const lab = sim.initialState();
  const device = lab.devices[1];
  device.connected = true;
  device.value = 20;
  lab.runs = [sim.createRun(device, 'control')];
  device.value = 75;
  device.enabled = true;
  assert.equal(sim.saveState(lab), true);
  const restored = sim.loadState();
  assert.equal(restored.runs[0].status, 'cancelled');
  assert.equal(restored.devices[1].connected, false);
  assert.equal(restored.devices[1].value, 20);
  assert.equal(restored.devices[1].enabled, false);
});
test('corrupt and incompatible storage recover to a default workspace', () => {
  for (const raw of [
    'bad json',
    '{"version":8}',
    '{"version":1,"devices":[{}],"runs":[],"logs":[]}',
  ]) {
    store.set('hardware-tester.lab.v1', raw);
    assert.equal(sim.loadState().devices.length, 3);
  }
});
test('duplicate device IDs are rejected', () => {
  const lab = sim.initialState();
  lab.devices[1].id = lab.devices[0].id;
  assert.equal(sim.isLabState(lab), false);
});
test('incomplete runs cannot be marked passed', () => {
  const run = sim.createRun(sim.createDevice('relay'), 'smoke');
  assert.equal(sim.finishRun(run).status, 'failed');
});
test('blocked storage does not crash the simulator', () => {
  const original = global.localStorage;
  global.localStorage = {
    getItem() {
      throw Error('blocked');
    },
    setItem() {
      throw Error('blocked');
    },
  };
  assert.equal(sim.saveState(sim.initialState()), false);
  assert.equal(sim.loadState().devices.length, 3);
  global.localStorage = original;
});
