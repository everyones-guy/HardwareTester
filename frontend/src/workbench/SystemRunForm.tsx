import { type FormEvent, useState } from 'react';
import type { ServerResponse } from './backend';
import type { TestRun } from './simulator';

async function jsonFile(fields: FormData, name: string) {
  const file = fields.get(name);
  if (!(file instanceof File) || !file.size || file.size > 64 * 1024) {
    throw new Error(`Choose a ${name} JSON file up to 64 KiB.`);
  }
  try {
    return JSON.parse(await file.text()) as unknown;
  } catch {
    throw new Error(`The ${name} file is invalid JSON.`);
  }
}

export default function SystemRunForm({
  disabled,
  releaseSha256,
  action,
  onResults,
}: {
  disabled: boolean;
  releaseSha256: string;
  action: (path: string, method?: string, payload?: unknown) => Promise<ServerResponse | undefined>;
  onResults: (run: TestRun) => void;
}) {
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function launch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    setError('');
    setSubmitting(true);
    try {
      const plan = await jsonFile(fields, 'plan');
      const bench = await jsonFile(fields, 'bench binding');
      const response = await action('/system-runs', 'POST', {
        plan,
        bench,
        releaseSha256: releaseSha256 || undefined,
      });
      const identity = response?.runId;
      const run = response?.state.runs.find((item) => item.id === identity);
      if (run) onResults(run);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'The system run could not be started.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <details className="bench-emulation">
      <summary>Run a multi-device system plan</summary>
      <form onSubmit={(event) => void launch(event)}>
        <fieldset disabled={disabled || submitting} className="firmware-fields">
          <label>
            System plan JSON
            <input name="plan" type="file" accept=".json" required />
          </label>
          <label>
            Bench binding JSON
            <input name="bench binding" type="file" accept=".json" required />
          </label>
          <button className="button primary" type="submit">
            Run system plan
          </button>
        </fieldset>
        {error && <p role="alert">{error}</p>}
        <p className="helper">
          Modeled bindings define states and readings. Connected bindings reference registered
          devices and require explicit approval for each relay.
        </p>
      </form>
    </details>
  );
}
