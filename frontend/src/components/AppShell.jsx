import { LogOut, Menu, ShieldCheck, X } from "lucide-react";
import { useState } from "react";

import { useAuth } from "../context/AuthContext";
import Brand from "./Brand";


export default function AppShell({ navigation, active, onNavigate, children }) {
    const { logout, user } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);

    function navigate(id) {
        onNavigate(id);
        setMobileOpen(false);
    }

    return (
        <div className="shell">
            <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
                <div className="sidebar-head">
                    <Brand />
                    <button className="icon-button mobile-only" onClick={() => setMobileOpen(false)}>
                        <X size={20} />
                    </button>
                </div>
                {user.role === "admin" && (
                    <div className="admin-badge"><ShieldCheck size={15} /> Admin workspace</div>
                )}
                <nav className="nav-list">
                    {navigation.map(({ id, label, icon: Icon }) => (
                        <button
                            type="button"
                            className={active === id ? "active" : ""}
                            key={id}
                            onClick={() => navigate(id)}
                        >
                            <Icon size={19} /> {label}
                        </button>
                    ))}
                </nav>
                <div className="sidebar-user">
                    <div className="avatar">{user.name?.charAt(0).toUpperCase()}</div>
                    <div><strong>{user.name}</strong><span>{user.email}</span></div>
                    <button className="icon-button" onClick={logout} title="Sign out">
                        <LogOut size={18} />
                    </button>
                </div>
            </aside>
            <main className="main-content">
                <button className="mobile-menu mobile-only" onClick={() => setMobileOpen(true)}>
                    <Menu size={21} /> Menu
                </button>
                {children}
            </main>
            {mobileOpen && <button className="sidebar-scrim mobile-only" onClick={() => setMobileOpen(false)} />}
        </div>
    );
}
