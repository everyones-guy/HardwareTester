import { useState } from 'react';

export interface Account {
  id: string;
  username: string;
  email: string;
  role: 'viewer' | 'operator' | 'admin';
  enabled: boolean;
  version: number;
}
export interface Session {
  enabled: boolean;
  setupRequired: boolean;
  user: Account | null;
  csrf: string | null;
}
let csrf = '';
export async function authRequest(path: string, method = 'GET', data?: unknown) {
  const response = await fetch('/api/auth' + path, {
    method,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
    body: data === undefined ? undefined : JSON.stringify(data),
    signal: AbortSignal.timeout(10000),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Account request failed.');
  if ('csrf' in result) csrf = result.csrf || '';
  return result;
}
export function csrfToken() {
  return csrf;
}

export function SignIn({
  session,
  onSession,
  error: connectionError = '',
}: {
  session: Session | undefined;
  onSession: (s: Session) => void;
  error?: string;
}) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <section className="panel settings-panel">
      <h2>{session?.setupRequired ? 'Create the first admin' : 'Sign in to HardwareTester'}</h2>
      <p>
        {session?.setupRequired
          ? 'This account will manage users and the shared workspace. Passwords require 12–128 characters.'
          : 'Use your account for this backend. Sessions last eight hours.'}
      </p>
      {(error || connectionError) && (
        <p role="alert" className="helper danger">
          {error || connectionError}
        </p>
      )}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError('');
          try {
            const result = await authRequest(session?.setupRequired ? '/setup' : '/login', 'POST', {
              username,
              email,
              password,
            });
            setPassword('');
            onSession(result);
          } catch (e) {
            setError(e instanceof Error ? e.message : 'Sign in failed.');
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Username
          <input
            aria-label="Sign in username"
            required
            autoComplete="username"
            value={username}
            maxLength={50}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        {session?.setupRequired && (
          <label>
            Email
            <input
              aria-label="Admin email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
        )}
        <label>
          Password
          <input
            aria-label="Sign in password"
            type="password"
            required
            minLength={session?.setupRequired ? 12 : 1}
            maxLength={128}
            autoComplete={session?.setupRequired ? 'new-password' : 'current-password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="button primary" disabled={busy || !session}>
          {busy ? 'Signing in…' : session?.setupRequired ? 'Create admin' : 'Sign in'}
        </button>
      </form>
    </section>
  );
}
