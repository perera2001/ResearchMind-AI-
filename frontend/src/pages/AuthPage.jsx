import { ArrowRight, BookOpen, Check, LockKeyhole, Mail, User } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Brand from "../components/Brand";
import { useAuth } from "../context/AuthContext";


export default function AuthPage() {
    const [mode, setMode] = useState("login");
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const { login, register } = useAuth();
    const navigate = useNavigate();

    async function submit(event) {
        event.preventDefault();
        setError("");
        setSubmitting(true);

        try {
            const user = mode === "login"
                ? await login(form.email, form.password)
                : await register(form.name, form.email, form.password);
            navigate(user.role === "admin" ? "/admin" : "/dashboard");
        } catch (requestError) {
            setError(requestError.message);
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="auth-layout">
            <section className="auth-story">
                <Brand />
                <div className="story-copy">
                    <span className="eyebrow">Your intelligent research companion</span>
                    <h1>Turn dense papers into clear insight.</h1>
                    <p>Upload your research library, select the papers that matter, and ask grounded questions across them in seconds.</p>
                    <div className="feature-list">
                        <span><Check size={17} /> Evidence grounded answers</span>
                        <span><Check size={17} /> Multi-paper comparison</span>
                        <span><Check size={17} /> Private research workspace</span>
                    </div>
                </div>
                <div className="paper-art" aria-hidden="true">
                    <div className="paper paper-one"><span /><span /><span /></div>
                    <div className="paper paper-two"><BookOpen size={42} /></div>
                    <div className="orb orb-one" /><div className="orb orb-two" />
                </div>
            </section>
            <section className="auth-panel">
                <div className="auth-card">
                    <span className="eyebrow">{mode === "login" ? "Welcome back" : "Start researching"}</span>
                    <h2>{mode === "login" ? "Sign in to your workspace" : "Create your account"}</h2>
                    <p>{mode === "login" ? "Continue exploring your research library." : "Build your private AI-powered paper library."}</p>
                    <form onSubmit={submit}>
                        {mode === "register" && (
                            <label>Full name<div className="input-wrap"><User size={18} /><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Your name" /></div></label>
                        )}
                        <label>Email address<div className="input-wrap"><Mail size={18} /><input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="you@example.com" /></div></label>
                        <label>Password<div className="input-wrap"><LockKeyhole size={18} /><input type="password" minLength={8} required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="At least 8 characters" /></div></label>
                        {error && <div className="form-error">{error}</div>}
                        <button className="primary-button auth-submit" disabled={submitting}>
                            {submitting ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
                            {!submitting && <ArrowRight size={18} />}
                        </button>
                    </form>
                    <div className="auth-switch">
                        {mode === "login" ? "New to ResearchMind?" : "Already have an account?"}
                        <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
                            {mode === "login" ? "Create an account" : "Sign in"}
                        </button>
                    </div>
                </div>
            </section>
        </div>
    );
}
