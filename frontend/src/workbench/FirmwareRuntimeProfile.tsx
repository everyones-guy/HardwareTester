import { type FormEvent, useEffect, useState } from 'react';
import { workspaceRequest } from './backend';

type RuntimeProfile = {
  releaseSha256: string;
  profileSha256: string;
  platform: string | null;
  baseImage: string | null;
  libcPackageVersion: string | null;
  entrypoint: { path: string; sha256: string };
  arguments: string[];
  status: 'readyForSmokeTest' | 'blocked';
  dependencies: { library: string; requiredBy: string; resolution: string; path?: string }[];
  diagnostics: string[];
};

type RuntimeResponse = {
  entrypoints: { path: string; sha256: string }[];
  profile: RuntimeProfile | null;
};

const resolutionLabels: Record<string, string> = {
  baseImage: 'Pinned base image',
  bundle: 'Release bundle',
  missing: 'Missing',
  ambiguous: 'Ambiguous',
  unsupportedPath: 'Unsupported path-based dependency',
};

export default function FirmwareRuntimeProfile({
  digest,
  saveFile,
}: {
  digest: string;
  saveFile: (file: Blob, name: string) => void;
}) {
  const [data, setData] = useState<RuntimeResponse>();
  const [entrypoint, setEntrypoint] = useState('');
  const [argument, setArgument] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const route = `/firmware/${digest}/runtime-profile`;
  useEffect(() => {
    let current = true;
    void workspaceRequest<RuntimeResponse>(route)
      .then((result) => {
        if (current) {
          setData(result);
          setEntrypoint(result.profile?.entrypoint.path ?? '');
        }
      })
      .catch((failure: Error) => {
        if (current) setError(failure.message);
      });
    return () => {
      current = false;
    };
  }, [route]);

  async function generate(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError('');
    const params = new URLSearchParams({ entrypoint });
    if (argument.trim()) params.set('argument', argument.trim());
    try {
      setData(await workspaceRequest<RuntimeResponse>(`${route}?${params}`));
    } catch (failure) {
      setError(
        failure instanceof Error ? failure.message : 'The runtime profile could not be generated.',
      );
    } finally {
      setPending(false);
    }
  }

  const profile = data?.profile;
  const current =
    profile &&
    profile.entrypoint.path === entrypoint &&
    (profile.arguments[0] ?? '') === argument.trim();
  return (
    <details>
      <summary>Runtime profile</summary>
      {error && <p role="alert">{error}</p>}
      {!data && !error && <p role="status">Reading inspected entry points…</p>}
      {data && !data.entrypoints.length && (
        <p>Upload a release ZIP with an inspected dynamic ELF to generate a profile.</p>
      )}
      {!!data?.entrypoints.length && (
        <form onSubmit={(event) => void generate(event)}>
          <fieldset className="firmware-fields" disabled={pending}>
            <label>
              Runtime entry point
              <select
                required
                value={entrypoint}
                onChange={(event) => setEntrypoint(event.target.value)}
              >
                <option value="">Choose an executable</option>
                {data.entrypoints.map(({ path }) => (
                  <option key={path} value={path}>
                    {path}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Optional smoke-test flag
              <input
                placeholder="--self-test"
                value={argument}
                maxLength={34}
                onChange={(event) => setArgument(event.target.value)}
              />
            </label>
            <button className="button" type="submit">
              Generate runtime profile
            </button>
          </fieldset>
        </form>
      )}
      {profile && current && (
        <section aria-label="Generated runtime profile">
          <p>
            <strong>{profile.status === 'blocked' ? 'Blocked' : 'Ready for smoke test'}</strong>
          </p>
          <dl>
            <dt>Platform</dt>
            <dd>{profile.platform ?? 'Unsupported'}</dd>
            <dt>Pinned image</dt>
            <dd>
              <code>{profile.baseImage ?? 'Unavailable'}</code>
            </dd>
            <dt>glibc package</dt>
            <dd>{profile.libcPackageVersion ?? 'Unavailable'}</dd>
            <dt>Profile SHA-256</dt>
            <dd>
              <code>{profile.profileSha256}</code>
            </dd>
          </dl>
          {profile.diagnostics.length > 0 && (
            <ul>
              {profile.diagnostics.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          )}
          {profile.dependencies.length > 0 && (
            <details>
              <summary>Library resolution ({profile.dependencies.length})</summary>
              <ul>
                {profile.dependencies.map((dependency) => (
                  <li key={`${dependency.requiredBy}:${dependency.library}`}>
                    <code>{dependency.library}</code> · {resolutionLabels[dependency.resolution]} ·{' '}
                    {dependency.requiredBy}
                    {dependency.path && ` → ${dependency.path}`}
                  </li>
                ))}
              </ul>
            </details>
          )}
          <p>
            Review the profile before running the release locally with{' '}
            <code>tools.run_firmware_runtime</code>.
          </p>
          <button
            className="button"
            type="button"
            disabled={pending}
            onClick={() =>
              saveFile(
                new Blob([JSON.stringify(profile, null, 2)], { type: 'application/json' }),
                `${digest}.runtime.json`,
              )
            }
          >
            Export runtime profile
          </button>
        </section>
      )}
    </details>
  );
}
