type Provider = { role?: string; deviceId?: string; name: string; adapter: string };
type RequestEntry = {
  requestId: string;
  idSource: 'wire' | 'local';
  operation: string;
  provider: string;
  phase: 'step' | 'restoration';
  stepIndex?: number;
  role?: string;
  startedAt: string;
  finishedAt: string;
  outcome: 'succeeded' | 'failed';
  requested?: number | boolean;
  observed?: number | boolean;
  error?: string;
};

export type AuditRecord = {
  kind: 'device' | 'system';
  operator: { id: string; username: string; role: string } | null;
  release: { sha256: string; name: string | null; version: string | null } | null;
  providers: Provider[];
  benchMode?: 'modeled' | 'connected';
  planSha256?: string;
  requests: RequestEntry[];
  droppedRequests: number;
  restorationByRole?: Record<string, string>;
  error?: string;
};

export default function RunAudit({ audit }: { audit: AuditRecord }) {
  return (
    <section className="run-audit" aria-label="Run provenance">
      <h3>Run provenance</h3>
      <p>
        Operator{' '}
        {audit.operator ? `${audit.operator.username} · ${audit.operator.role}` : 'unattributed'}
      </p>
      <p>
        Selected release{' '}
        {audit.release ? (
          <>
            {audit.release.name ?? 'Selected by digest'} {audit.release.version} ·{' '}
            <code>{audit.release.sha256}</code>
          </>
        ) : (
          'unrecorded'
        )}
      </p>
      {audit.planSha256 && (
        <p>
          Plan SHA-256 <code>{audit.planSha256}</code>
        </p>
      )}
      <p>
        Providers{' '}
        {audit.providers
          .map(
            (provider) =>
              `${provider.role ? `${provider.role} · ` : ''}${provider.name} (${provider.adapter})`,
          )
          .join('; ')}
      </p>
      {audit.restorationByRole && Object.keys(audit.restorationByRole).length > 0 && (
        <ul aria-label="Restoration by role">
          {Object.entries(audit.restorationByRole).map(([role, result]) => (
            <li key={role}>
              {role} · {result}
            </li>
          ))}
        </ul>
      )}
      {audit.error && <p className="danger">{audit.error}</p>}
      <details>
        <summary>Correlated requests ({audit.requests.length})</summary>
        {audit.droppedRequests > 0 && (
          <p>{audit.droppedRequests} later requests exceeded the per-run recording limit.</p>
        )}
        <ol>
          {audit.requests.map((event) => (
            <li key={event.requestId}>
              <strong>
                {event.operation} · {event.outcome}
              </strong>{' '}
              · {event.role ?? event.provider} ·{' '}
              {event.phase === 'restoration' ? 'Restoration' : `Step ${(event.stepIndex ?? 0) + 1}`}
              <div>
                <code>{event.requestId}</code> ·{' '}
                {event.idSource === 'wire' ? 'Wire ID' : 'Local ID'}
              </div>
              <div>
                <time dateTime={event.startedAt}>{event.startedAt}</time> →{' '}
                <time dateTime={event.finishedAt}>{event.finishedAt}</time>
              </div>
              {event.requested !== undefined && <div>Requested {String(event.requested)}</div>}
              {event.observed !== undefined && <div>Observed {String(event.observed)}</div>}
              {event.error && <div className="danger">{event.error}</div>}
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}
