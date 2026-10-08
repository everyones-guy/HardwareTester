import { useEffect, useState } from 'react';
import {
  FiChevronDown,
  FiChevronLeft,
  FiChevronRight,
  FiPlus,
  FiSearch,
  FiShield,
  FiUser,
  FiX,
} from 'react-icons/fi';
import { Account, authRequest } from './Accounts';
import './user-directory.css';

const roles = {
  viewer: 'Inspect devices and export results.',
  operator: 'Connect and control devices, run tests, and inspect results.',
  admin: 'Manage accounts, device configuration, and the shared workspace.',
};
const initials = (name: string) =>
  name
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

export default function UserManagement({
  onChange,
  currentUserId,
}: {
  onChange: () => void;
  currentUserId?: string;
}) {
  const [users, setUsers] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState('');
  const [query, setQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(0);
  const [rows, setRows] = useState(5);
  const [creating, setCreating] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Account['role']>('viewer');
  const [resetting, setResetting] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      setUsers((await authRequest('/users')).users);
      setError('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load accounts.');
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  const filtered = users
    .filter(
      (u) =>
        (u.username + ' ' + u.email).toLowerCase().includes(query.toLowerCase()) &&
        (roleFilter === 'all' || u.role === roleFilter) &&
        (statusFilter === 'all' || (statusFilter === 'enabled') === u.enabled),
    )
    .sort((a, b) => a.username.localeCompare(b.username));
  const lastPage = Math.max(0, Math.ceil(filtered.length / rows) - 1);
  const currentPage = Math.min(page, lastPage);
  const visible = filtered.slice(currentPage * rows, (currentPage + 1) * rows);
  const enabled = users.filter((u) => u.enabled).length;
  const admins = users.filter((u) => u.enabled && u.role === 'admin').length;
  function filter(fn: () => void) {
    fn();
    setPage(0);
    setExpanded('');
    setResetting('');
  }
  async function update(user: Account, changes: Record<string, unknown>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await authRequest(`/users/${user.id}`, 'PATCH', {
        version: user.version,
        ...changes,
      });
      setUsers(result.users);
      setNotice(`Updated ${user.username}.`);
      onChange();
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Account update failed.');
      await load();
      return false;
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel user-directory" aria-labelledby="directory-heading">
      <header className="directory-heading">
        <div>
          <span className="eyebrow">ACCESS DIRECTORY / PERSONNEL</span>
          <h2 id="directory-heading">User accounts</h2>
          <p>A place for everyone on the bench.</p>
        </div>
        <button
          className="button primary"
          disabled={busy}
          aria-expanded={creating}
          onClick={() => {
            setCreating(!creating);
            setPassword('');
          }}
        >
          {creating ? <FiX /> : <FiPlus />}
          {creating ? 'Close new account' : 'New account'}
        </button>
      </header>
      <div className="directory-meters">
        <span>
          <b>{String(users.length).padStart(2, '0')}</b> ACCOUNTS
        </span>
        <span>
          <i className="directory-led enabled" />
          <b>{String(enabled).padStart(2, '0')}</b> ENABLED
        </span>
        <span>
          <FiShield />
          <b>{String(admins).padStart(2, '0')}</b> ADMINS
        </span>
      </div>
      {error && (
        <div className="directory-message failure" role="alert">
          {error}
          <button className="text-button" disabled={busy} onClick={() => void load()}>
            Reload directory
          </button>
        </div>
      )}
      {notice && (
        <div className="directory-message" role="status">
          {notice}
        </div>
      )}
      {creating && (
        <form
          className="directory-create"
          aria-label="New account"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError('');
            try {
              const result = await authRequest('/users', 'POST', {
                username,
                email,
                password,
                role,
              });
              setUsers(result.users);
              const created = result.users.find(
                (u: Account) => u.username === username.trim().toLowerCase(),
              );
              setExpanded(created?.id || '');
              setQuery('');
              setRoleFilter('all');
              setStatusFilter('all');
              setPage(
                created
                  ? Math.floor(
                      [...result.users]
                        .sort((a: Account, b: Account) => a.username.localeCompare(b.username))
                        .findIndex((u: Account) => u.id === created.id) / rows,
                    )
                  : 0,
              );
              setNotice(`Created ${username.trim().toLowerCase()}.`);
              setUsername('');
              setEmail('');
              setPassword('');
              setCreating(false);
            } catch (e) {
              setError(e instanceof Error ? e.message : 'Could not create account.');
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="directory-section-title">
            <FiUser />
            <h3>Issue a new account</h3>
          </div>
          <div className="directory-form-grid">
            <label>
              Username
              <input
                aria-label="New username"
                required
                value={username}
                maxLength={50}
                autoComplete="off"
                onChange={(e) => setUsername(e.target.value)}
              />
            </label>
            <label>
              Email
              <input
                aria-label="New user email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label>
              Temporary password
              <input
                aria-label="New user password"
                type="password"
                required
                minLength={12}
                maxLength={128}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <label>
              Access role
              <select
                aria-label="New user role"
                value={role}
                onChange={(e) => setRole(e.target.value as Account['role'])}
              >
                {Object.keys(roles).map((r) => (
                  <option value={r} key={r}>
                    {r[0].toUpperCase() + r.slice(1)}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className="directory-help">Passwords require 12–128 characters. {roles[role]}</p>
          <button className="button primary" disabled={busy}>
            {busy ? 'Creating…' : 'Create account'}
          </button>
        </form>
      )}
      <div className="directory-toolbar">
        <label className="directory-search">
          <FiSearch />
          <input
            aria-label="Search accounts"
            placeholder="Find a name or email…"
            value={query}
            onChange={(e) => filter(() => setQuery(e.target.value))}
          />
        </label>
        <label>
          Status
          <select
            aria-label="Filter account status"
            value={statusFilter}
            onChange={(e) => filter(() => setStatusFilter(e.target.value))}
          >
            <option value="all">All statuses</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
          </select>
        </label>
        <label>
          Rows
          <select
            aria-label="Visible account rows"
            value={rows}
            onChange={(e) => filter(() => setRows(Number(e.target.value)))}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n} at a time
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="directory-tabs" role="group" aria-label="Filter accounts by role">
        {['all', ...Object.keys(roles)].map((r) => (
          <button
            key={r}
            className={roleFilter === r ? 'selected' : ''}
            aria-pressed={roleFilter === r}
            onClick={() => filter(() => setRoleFilter(r))}
          >
            {r === 'all' ? 'Everyone' : r[0].toUpperCase() + r.slice(1)}
            <small>{r === 'all' ? users.length : users.filter((u) => u.role === r).length}</small>
          </button>
        ))}
      </div>
      <div className="directory-tray">
        <div className="directory-tray-label">
          <span>ACCOUNT INDEX</span>
          <span>A—Z / {String(filtered.length).padStart(2, '0')} RECORDS</span>
        </div>
        {loading ? (
          <p className="empty" role="status">
            Loading account directory…
          </p>
        ) : !visible.length ? (
          <div className="directory-empty">
            <FiSearch />
            <h3>No accounts match</h3>
            <p>Try another name, role, or status.</p>
            <button
              className="button secondary"
              onClick={() =>
                filter(() => {
                  setQuery('');
                  setRoleFilter('all');
                  setStatusFilter('all');
                })
              }
            >
              Clear filters
            </button>
          </div>
        ) : (
          visible.map((u, index) => {
            const open = expanded === u.id;
            const lastAdmin = u.enabled && u.role === 'admin' && admins === 1;
            return (
              <article
                className={`directory-card ${open ? 'expanded' : ''} ${!u.enabled ? 'is-disabled' : ''}`}
                key={u.id}
              >
                <button
                  className="directory-row"
                  aria-label={`Account ${u.username}`}
                  aria-expanded={open}
                  aria-controls={`account-${u.id}`}
                  onClick={() => {
                    setExpanded(open ? '' : u.id);
                    setResetting('');
                  }}
                >
                  <span className="directory-index">
                    {String(currentPage * rows + index + 1).padStart(2, '0')}
                  </span>
                  <span className={`directory-avatar role-${u.role}`} aria-hidden="true">
                    {initials(u.username)}
                  </span>
                  <span className="directory-person">
                    <strong>
                      {u.username}
                      {u.id === currentUserId && <small>YOU</small>}
                    </strong>
                    <span>{u.email}</span>
                  </span>
                  <span className={`directory-role role-${u.role}`}>{u.role}</span>
                  <span className="directory-state">
                    <i className={`directory-led ${u.enabled ? 'enabled' : 'disabled'}`} />
                    {u.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <FiChevronDown className="directory-chevron" />
                </button>
                {open && (
                  <div className="directory-details" id={`account-${u.id}`}>
                    <div className="directory-detail-heading">
                      <span className="eyebrow">ACCOUNT RECORD</span>
                      <span className="directory-record">
                        REV {String(u.version).padStart(2, '0')}
                      </span>
                    </div>
                    <h3>{u.username}</h3>
                    <dl className="directory-facts">
                      <div>
                        <dt>Email</dt>
                        <dd>{u.email}</dd>
                      </div>
                      <div>
                        <dt>Account ID</dt>
                        <dd>{u.id}</dd>
                      </div>
                      <div>
                        <dt>Access</dt>
                        <dd>{roles[u.role]}</dd>
                      </div>
                    </dl>
                    <div className="directory-controls">
                      <label>
                        Access role
                        <select
                          aria-label={`Role for ${u.username}`}
                          value={u.role}
                          disabled={busy || lastAdmin}
                          onChange={(e) => void update(u, { role: e.target.value })}
                        >
                          {Object.keys(roles).map((r) => (
                            <option value={r} key={r}>
                              {r[0].toUpperCase() + r.slice(1)}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div>
                        <button
                          className={`button secondary ${u.enabled ? 'danger' : ''}`}
                          disabled={busy || lastAdmin}
                          onClick={() => {
                            if (
                              confirm(
                                `${u.enabled ? 'Disable' : 'Enable'} ${u.username}?${u.enabled ? ' Their active sessions will be revoked.' : ''}`,
                              )
                            )
                              void update(u, { enabled: !u.enabled });
                          }}
                        >
                          {u.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          className="button secondary"
                          disabled={busy}
                          aria-expanded={resetting === u.id}
                          onClick={() => setResetting(resetting === u.id ? '' : u.id)}
                        >
                          Reset password
                        </button>
                      </div>
                    </div>
                    {lastAdmin && (
                      <p className="directory-help">
                        <FiShield /> This is the last enabled admin. Add another admin before
                        changing its access.
                      </p>
                    )}
                    {resetting === u.id && (
                      <form
                        className="directory-password"
                        onSubmit={async (e) => {
                          e.preventDefault();
                          const form = e.currentTarget;
                          const value = String(new FormData(form).get('password'));
                          if (await update(u, { password: value })) {
                            form.reset();
                            setResetting('');
                          }
                        }}
                      >
                        <label>
                          New password
                          <input
                            aria-label={`Password for ${u.username}`}
                            name="password"
                            type="password"
                            required
                            minLength={12}
                            maxLength={128}
                            autoComplete="new-password"
                          />
                        </label>
                        <p className="directory-help">
                          Changing the password signs this account out of every session.
                        </p>
                        <button className="button primary" disabled={busy}>
                          Set password
                        </button>
                      </form>
                    )}
                  </div>
                )}
              </article>
            );
          })
        )}
      </div>
      <footer className="directory-footer">
        <span>
          {filtered.length
            ? `${currentPage * rows + 1}–${Math.min((currentPage + 1) * rows, filtered.length)} of ${filtered.length} accounts`
            : '0 accounts'}
          <small>SELECT A ROW TO OPEN ITS RECORD</small>
        </span>
        <div>
          <button
            className="icon-button"
            aria-label="Previous account page"
            disabled={currentPage === 0}
            onClick={() => {
              setPage(currentPage - 1);
              setExpanded('');
              setResetting('');
            }}
          >
            <FiChevronLeft />
          </button>
          <span>
            {currentPage + 1} / {lastPage + 1}
          </span>
          <button
            className="icon-button"
            aria-label="Next account page"
            disabled={currentPage >= lastPage}
            onClick={() => {
              setPage(currentPage + 1);
              setExpanded('');
              setResetting('');
            }}
          >
            <FiChevronRight />
          </button>
        </div>
      </footer>
    </section>
  );
}
