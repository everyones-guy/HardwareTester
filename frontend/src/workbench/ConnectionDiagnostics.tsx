import { FiActivity } from 'react-icons/fi';
import { Device } from './simulator';
import './connection-diagnostics.css';

export default function ConnectionDiagnostics({
  device,
  disabled,
  onCheck,
}: {
  device: Device;
  disabled: boolean;
  onCheck: () => void;
}) {
  const checks = device.diagnostics ?? [];
  return (
    <section
      className="inspector-section connection-diagnostics"
      aria-label="Connection diagnostics"
    >
      <span className="eyebrow">CONNECTION DIAGNOSTICS</span>
      <dl>
        <div>
          <dt>Adapter</dt>
          <dd>{device.adapter ?? 'simulation'}</dd>
        </div>
        <div>
          <dt>Endpoint</dt>
          <dd>{device.endpoint}</dd>
        </div>
        <div>
          <dt>Last response</dt>
          <dd>
            {device.lastContactAt
              ? new Date(device.lastContactAt).toLocaleString()
              : 'No response recorded'}
          </dd>
        </div>
      </dl>
      <button className="button secondary full" disabled={disabled} onClick={onCheck}>
        <FiActivity />
        Test connection
      </button>
      <p className="helper">
        Reads telemetry from the current connection. Connect first; checks pause during test runs.
      </p>
      {!checks.length ? (
        <p className="helper">No connection checks yet.</p>
      ) : (
        <ol className="connection-checks" aria-label="Recent connection checks">
          {checks.map((c, i) => (
            <li key={`${c.checkedAt}-${i}`} className={`connection-check ${c.status}`}>
              <div>
                <strong>
                  {c.status === 'passed'
                    ? 'Responding'
                    : c.status === 'warning'
                      ? 'Reading out of range'
                      : 'No response'}
                </strong>
                <span>{c.durationMs} ms</span>
              </div>
              <p>{c.detail}</p>
              <time dateTime={c.checkedAt}>
                {new Date(c.checkedAt).toLocaleString()}
                {device.adapter === undefined || device.adapter === 'simulation'
                  ? ' · simulated'
                  : ''}
              </time>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
