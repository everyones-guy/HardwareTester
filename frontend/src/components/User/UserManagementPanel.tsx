// src/components/User/UserManagementPanel.tsx
import React, { useEffect, useMemo, useState } from "react";
import UserService from "@/services/userService";
import { User } from "@/types/userTypes";
import ModalWrapper from "@/components/common/ModalWrapper";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import Button from "@/components/common/Button";

type RoleOption = "Admin" | "Tester" | "Viewer" | "All";

interface FormState {
    id?: string;
    username: string;
    email: string;
    role: "Admin" | "Tester" | "Viewer";
    isActive: boolean;
}

const emptyForm: FormState = {
    username: "",
    email: "",
    role: "Viewer",
    isActive: true,
};

const UserManagementPanel: React.FC = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // filters
    const [query, setQuery] = useState("");
    const [roleFilter, setRoleFilter] = useState<RoleOption>("All");
    const [activeOnly, setActiveOnly] = useState(false);

    // modals
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState<FormState>(emptyForm);
    const [showDelete, setShowDelete] = useState(false);
    const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

    // fetch users
    const fetchUsers = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await UserService.listUsers();
            // Expecting { success, data: { users: User[] } } shape; fall back if different
            const list: User[] =
                // @ts-ignore - tolerate various API envelopes
                res?.data?.users ?? res?.users ?? [];
            setUsers(Array.isArray(list) ? list : []);
        } catch (e: any) {
            setError(e?.message || "Failed to load users.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    // filters + search
    const filtered = useMemo(() => {
        return users
            .filter((u) =>
                roleFilter === "All" ? true : u.role === roleFilter
            )
            .filter((u) => (activeOnly ? u.isActive : true))
            .filter((u) => {
                if (!query.trim()) return true;
                const q = query.toLowerCase();
                return (
                    u.username.toLowerCase().includes(q) ||
                    u.email.toLowerCase().includes(q) ||
                    u.role.toLowerCase().includes(q)
                );
            });
    }, [users, roleFilter, activeOnly, query]);

    // open add/edit
    const openAdd = () => {
        setForm(emptyForm);
        setShowForm(true);
    };

    const openEdit = (u: User) => {
        setForm({
            id: u.id,
            username: u.username,
            email: u.email,
            role: u.role,
            isActive: u.isActive,
        });
        setShowForm(true);
    };

    // save (add or update)
    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        try {
            const payload = {
                username: form.username.trim(),
                email: form.email.trim(),
                role: form.role,
                // If your backend supports isActive on update, include it there.
            };

            if (!payload.username || !payload.email) {
                setError("Username and email are required.");
                setSaving(false);
                return;
            }

            if (form.id) {
                await UserService.updateUser(form.id, {
                    ...payload,
                    // optionally include isActive on update if supported
                    // @ts-ignore
                    isActive: form.isActive,
                });
            } else {
                await UserService.addUser(payload);
            }

            setShowForm(false);
            await fetchUsers();
        } catch (e: any) {
            setError(e?.message || "Failed to save user.");
        } finally {
            setSaving(false);
        }
    };

    // delete
    const requestDelete = (id: string) => {
        setPendingDeleteId(id);
        setShowDelete(true);
    };

    const confirmDelete = async () => {
        if (!pendingDeleteId) return;
        setSaving(true);
        setError(null);
        try {
            await UserService.deleteUser(pendingDeleteId);
            setShowDelete(false);
            setPendingDeleteId(null);
            await fetchUsers();
        } catch (e: any) {
            setError(e?.message || "Failed to delete user.");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="user-management-panel">
            <div className="panel-header">
                <h2>Manage Users</h2>
                <div className="controls" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                    <input
                        placeholder="Search username, email, role..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value as RoleOption)}>
                        <option value="All">All Roles</option>
                        <option value="Admin">Admin</option>
                        <option value="Tester">Tester</option>
                        <option value="Viewer">Viewer</option>
                    </select>
                    <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <input
                            type="checkbox"
                            checked={activeOnly}
                            onChange={(e) => setActiveOnly(e.target.checked)}
                        />
                        Active only
                    </label>
                    <Button onClick={openAdd}>Add User</Button>
                    <Button variant="secondary" onClick={fetchUsers}>Refresh</Button>
                </div>
            </div>

            {error && (
                <div className="error" style={{ marginTop: 8 }}>
                    {error}
                </div>
            )}

            <div className="table-wrap" style={{ marginTop: 12 }}>
                {loading ? (
                    <div>Loading users…</div>
                ) : filtered.length === 0 ? (
                    <div>No users found.</div>
                ) : (
                    <table className="users-table">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Active</th>
                                <th>Last Login</th>
                                <th>Created</th>
                                <th style={{ width: 160 }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((u) => (
                                <tr key={u.id}>
                                    <td>{u.username}</td>
                                    <td>{u.email}</td>
                                    <td>{u.role}</td>
                                    <td>{u.isActive ? "Yes" : "No"}</td>
                                    <td>{u.lastLogin ?? "-"}</td>
                                    <td>{u.createdAt}</td>
                                    <td>
                                        <div style={{ display: "flex", gap: 8 }}>
                                            <Button size="sm" onClick={() => openEdit(u)}>Edit</Button>
                                            <Button size="sm" variant="danger" onClick={() => requestDelete(u.id)}>
                                                Delete
                                            </Button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Add / Edit Modal */}
            <ModalWrapper isOpen={showForm} onClose={() => setShowForm(false)} title={form.id ? "Edit User" : "Add User"}>
                <form onSubmit={handleSave} className="user-form" style={{ display: "grid", gap: 12 }}>
                    <label>
                        <span>Username</span>
                        <input
                            value={form.username}
                            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                            required
                        />
                    </label>
                    <label>
                        <span>Email</span>
                        <input
                            type="email"
                            value={form.email}
                            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                            required
                        />
                    </label>
                    <label>
                        <span>Role</span>
                        <select
                            value={form.role}
                            onChange={(e) =>
                                setForm((f) => ({ ...f, role: e.target.value as FormState["role"] }))
                            }
                        >
                            <option value="Admin">Admin</option>
                            <option value="Tester">Tester</option>
                            <option value="Viewer">Viewer</option>
                        </select>
                    </label>

                    {/* Only show active toggle in edit mode if your backend supports it */}
                    {form.id && (
                        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <input
                                type="checkbox"
                                checked={form.isActive}
                                onChange={(e) => setForm((f) => ({ ...f, isActive: e.target.checked }))}
                            />
                            Active
                        </label>
                    )}

                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 8 }}>
                        <Button type="button" variant="secondary" onClick={() => setShowForm(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={saving}>
                            {saving ? "Saving..." : form.id ? "Update" : "Create"}
                        </Button>
                    </div>
                </form>
            </ModalWrapper>

            {/* Delete confirm */}
            <ConfirmDialog
                open={showDelete}
                title="Delete user?"
                message="This action cannot be undone."
                onCancel={() => setShowDelete(false)}
                onConfirm={confirmDelete}
                confirmText={saving ? "Deleting..." : "Delete"}
                disableConfirm={saving}
            />
        </div>
    );
};

export default UserManagementPanel;
