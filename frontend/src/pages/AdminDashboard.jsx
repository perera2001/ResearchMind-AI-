import {
    BookOpenCheck,
    CalendarDays,
    LayoutDashboard,
    Search,
    ShieldCheck,
    Trash2,
    Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import AppShell from "../components/AppShell";
import ResearchWorkspace from "../components/ResearchWorkspace";
import Toast from "../components/Toast";
import { apiRequest } from "../lib/api";


function formatDate(value) {
    return new Intl.DateTimeFormat("en", {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(new Date(value.replace(" ", "T")));
}


function UsersPanel() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [query, setQuery] = useState("");
    const [toast, setToast] = useState(null);

    const loadUsers = useCallback(async () => {
        try {
            setUsers(await apiRequest("/admin/users"));
        } catch (error) {
            setToast({ type: "error", message: error.message });
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadUsers(); }, [loadUsers]);

    const filtered = useMemo(() => {
        const clean = query.toLowerCase().trim();
        return clean
            ? users.filter((user) => `${user.name} ${user.email}`.toLowerCase().includes(clean))
            : users;
    }, [query, users]);

    async function removeUser(user) {
        if (!window.confirm(`Delete ${user.name} and all of their PDFs and conversations? This cannot be undone.`)) return;

        try {
            await apiRequest(`/admin/users/${user.id}`, { method: "DELETE" });
            setUsers((current) => current.filter((item) => item.id !== user.id));
            setToast({ type: "success", message: `${user.name} was deleted.` });
        } catch (error) {
            setToast({ type: "error", message: error.message });
        }
    }

    return (
        <div className="admin-page">
            <header className="page-header"><div><span className="eyebrow">Administration</span><h1>User management</h1><p>Review registered researchers and manage account access.</p></div></header>
            <div className="stats-grid">
                <div className="stat-card"><span><Users size={20} /></span><div><small>Registered users</small><strong>{users.length}</strong></div></div>
                <div className="stat-card"><span><CalendarDays size={20} /></span><div><small>Joined this month</small><strong>{users.filter((user) => new Date(user.created_at).getMonth() === new Date().getMonth()).length}</strong></div></div>
                <div className="stat-card"><span><ShieldCheck size={20} /></span><div><small>Account type</small><strong>Regular users</strong></div></div>
            </div>
            <section className="users-card panel">
                <div className="users-toolbar"><div><h2>All researchers</h2><p>Only regular user accounts are shown.</p></div><label className="search-box"><Search size={17} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search users…" /></label></div>
                <div className="table-wrap">
                    <table>
                        <thead><tr><th>User</th><th>Role</th><th>Registered</th><th aria-label="Actions" /></tr></thead>
                        <tbody>
                            {filtered.map((user) => <tr key={user.id}><td><div className="table-user"><span>{user.name.charAt(0).toUpperCase()}</span><div><strong>{user.name}</strong><small>{user.email} · ID {user.id}</small></div></div></td><td><span className="role-pill">{user.role}</span></td><td>{formatDate(user.created_at)}</td><td><button className="danger-button" onClick={() => removeUser(user)}><Trash2 size={15} /> Delete</button></td></tr>)}
                            {!loading && filtered.length === 0 && <tr><td colSpan="4"><div className="table-empty">No users found.</div></td></tr>}
                            {loading && <tr><td colSpan="4"><div className="table-empty">Loading users…</div></td></tr>}
                        </tbody>
                    </table>
                </div>
            </section>
            <Toast {...toast} onClose={() => setToast(null)} />
        </div>
    );
}


function AdminOverview({ onNavigate }) {
    return (
        <div className="admin-page">
            <header className="page-header"><div><span className="eyebrow">Control center</span><h1>Admin dashboard</h1><p>Manage researchers and use your private research workspace.</p></div></header>
            <div className="admin-hero panel"><div><span className="admin-hero-icon"><ShieldCheck size={30} /></span><span className="eyebrow">ResearchMind administration</span><h2>Your platform, clearly organized.</h2><p>User management stays separate from your personal research data. Your PDFs and chats remain isolated under your admin account.</p></div></div>
            <div className="admin-actions">
                <button className="action-card" onClick={() => onNavigate("users")}><span><Users size={23} /></span><div><h3>Manage users</h3><p>View registrations and safely remove accounts and their associated data.</p></div><b>Open directory →</b></button>
                <button className="action-card" onClick={() => onNavigate("research")}><span><BookOpenCheck size={23} /></span><div><h3>Research workspace</h3><p>Upload admin-owned papers and ask grounded questions across selected PDFs.</p></div><b>Start researching →</b></button>
            </div>
        </div>
    );
}


export default function AdminDashboard() {
    const [active, setActive] = useState("overview");
    const navigation = [
        { id: "overview", label: "Overview", icon: LayoutDashboard },
        { id: "users", label: "User management", icon: Users },
        { id: "research", label: "Research workspace", icon: BookOpenCheck },
    ];

    return (
        <AppShell navigation={navigation} active={active} onNavigate={setActive}>
            {active === "overview" && <AdminOverview onNavigate={setActive} />}
            {active === "users" && <UsersPanel />}
            {active === "research" && <ResearchWorkspace heading="Admin research workspace" />}
        </AppShell>
    );
}
