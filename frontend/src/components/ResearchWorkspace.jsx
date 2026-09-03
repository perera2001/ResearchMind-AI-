import {
    Bot,
    CheckCircle2,
    ChevronRight,
    FileText,
    LoaderCircle,
    MessageSquare,
    Plus,
    Send,
    Sparkles,
    Trash2,
    UploadCloud,
    UserRound,
    X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { apiRequest } from "../lib/api";
import Toast from "./Toast";


function dateLabel(value) {
    if (!value) return "";
    return new Intl.DateTimeFormat("en", {
        month: "short",
        day: "numeric",
        year: "numeric",
    }).format(new Date(value.replace(" ", "T")));
}


export default function ResearchWorkspace({ heading = "Research workspace" }) {
    const [documents, setDocuments] = useState([]);
    const [selectedIds, setSelectedIds] = useState([]);
    const [sessions, setSessions] = useState([]);
    const [activeSession, setActiveSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [question, setQuestion] = useState("");
    const [uploading, setUploading] = useState(false);
    const [asking, setAsking] = useState(false);
    const [dragging, setDragging] = useState(false);
    const [toast, setToast] = useState(null);
    const fileInput = useRef(null);
    const messageEnd = useRef(null);

    const loadDocuments = useCallback(async () => {
        try {
            setDocuments(await apiRequest("/documents"));
        } catch (error) {
            setToast({ type: "error", message: error.message });
        }
    }, []);

    const loadSessions = useCallback(async () => {
        try {
            setSessions(await apiRequest("/chat/sessions"));
        } catch (error) {
            setToast({ type: "error", message: error.message });
        }
    }, []);

    useEffect(() => {
        loadDocuments();
        loadSessions();
    }, [loadDocuments, loadSessions]);

    useEffect(() => {
        messageEnd.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, asking]);

    async function uploadFiles(fileList) {
        const files = [...fileList].filter((file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"));

        if (!files.length) {
            setToast({ type: "error", message: "Please select PDF files." });
            return;
        }

        if (files.length > 10) {
            setToast({ type: "error", message: "You can upload up to 10 PDFs at once." });
            return;
        }

        const body = new FormData();
        files.forEach((file) => body.append("files", file));
        setUploading(true);

        try {
            const result = await apiRequest("/documents/upload", { method: "POST", body });
            const uploaded = result.documents || [result];
            setToast({
                type: result.errors?.length ? "error" : "success",
                message: result.errors?.length
                    ? `${uploaded.length} uploaded, ${result.errors.length} failed.`
                    : `${uploaded.length} PDF${uploaded.length === 1 ? "" : "s"} uploaded successfully.`,
            });
            await loadDocuments();
            setSelectedIds((current) => [...new Set([...current, ...uploaded.map((doc) => doc.id)])]);
        } catch (error) {
            setToast({ type: "error", message: error.message });
        } finally {
            setUploading(false);
            if (fileInput.current) fileInput.current.value = "";
        }
    }

    async function deleteDocument(id) {
        if (!window.confirm("Delete this PDF and all of its indexed content?")) return;

        try {
            await apiRequest(`/documents/${id}`, { method: "DELETE" });
            setDocuments((current) => current.filter((doc) => doc.id !== id));
            setSelectedIds((current) => current.filter((item) => item !== id));
            setToast({ type: "success", message: "Document deleted." });
        } catch (error) {
            setToast({ type: "error", message: error.message });
        }
    }

    function toggleDocument(id) {
        setSelectedIds((current) => current.includes(id)
            ? current.filter((item) => item !== id)
            : [...current, id]);
    }

    async function openSession(id) {
        try {
            const data = await apiRequest(`/chat/sessions/${id}`);
            setActiveSession(data.session);
            setMessages(data.messages);
        } catch (error) {
            setToast({ type: "error", message: error.message });
        }
    }

    async function deleteSession(event, id) {
        event.stopPropagation();
        if (!window.confirm("Delete this conversation?")) return;

        try {
            await apiRequest(`/chat/sessions/${id}`, { method: "DELETE" });
            setSessions((current) => current.filter((session) => session.id !== id));
            if (activeSession?.id === id) startNewChat();
        } catch (error) {
            setToast({ type: "error", message: error.message });
        }
    }

    function startNewChat() {
        setActiveSession(null);
        setMessages([]);
        setQuestion("");
    }

    async function ask(event) {
        event.preventDefault();
        const cleanQuestion = question.trim();
        if (!cleanQuestion || asking) return;
        if (!selectedIds.length) {
            setToast({ type: "error", message: "Select at least one processed PDF first." });
            return;
        }

        setQuestion("");
        setMessages((current) => [...current, { role: "user", content: cleanQuestion }]);
        setAsking(true);

        try {
            const result = await apiRequest("/chat", {
                method: "POST",
                body: JSON.stringify({
                    question: cleanQuestion,
                    session_id: activeSession?.id || null,
                    document_ids: selectedIds,
                }),
            });
            setMessages((current) => [...current, {
                role: "assistant",
                content: result.answer,
                sources: result.sources,
            }]);
            if (!activeSession) setActiveSession({ id: result.session_id, title: cleanQuestion.slice(0, 80) });
            await loadSessions();
        } catch (error) {
            setMessages((current) => current.slice(0, -1));
            setQuestion(cleanQuestion);
            setToast({ type: "error", message: error.message });
        } finally {
            setAsking(false);
        }
    }

    const processedDocuments = documents.filter((doc) => doc.status === "processed");

    return (
        <div className="workspace-page">
            <header className="page-header">
                <div><span className="eyebrow">Knowledge studio</span><h1>{heading}</h1><p>Select your sources and start a grounded conversation.</p></div>
                <button className="secondary-button" onClick={() => fileInput.current?.click()}><Plus size={18} /> Add papers</button>
            </header>

            <div className="research-grid">
                <section className="source-panel panel">
                    <div className="panel-heading"><div><span className="section-kicker">01 · Sources</span><h2>Your papers</h2></div><span className="count-pill">{documents.length}</span></div>
                    <button
                        type="button"
                        className={`dropzone ${dragging ? "dragging" : ""}`}
                        onClick={() => fileInput.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={(e) => { e.preventDefault(); setDragging(false); uploadFiles(e.dataTransfer.files); }}
                    >
                        {uploading ? <LoaderCircle className="spin" size={25} /> : <UploadCloud size={25} />}
                        <strong>{uploading ? "Processing your papers…" : "Drop PDFs here"}</strong>
                        <span>or click to browse · up to 10 files</span>
                    </button>
                    <input ref={fileInput} hidden type="file" accept="application/pdf,.pdf" multiple onChange={(e) => uploadFiles(e.target.files)} />
                    <div className="document-list">
                        {documents.length === 0 && <div className="empty-small"><FileText size={24} /><span>No papers uploaded yet</span></div>}
                        {documents.map((doc) => {
                            const ready = doc.status === "processed";
                            return (
                                <div className={`document-item ${selectedIds.includes(doc.id) ? "selected" : ""}`} key={doc.id}>
                                    <button className="document-select" disabled={!ready} onClick={() => toggleDocument(doc.id)}>
                                        <span className="pdf-icon">PDF</span>
                                        <span className="document-meta"><strong title={doc.file_name}>{doc.file_name}</strong><small>{ready ? `${doc.page_count} pages · ${doc.chunk_count} chunks` : doc.status}</small></span>
                                        <span className="select-check">{selectedIds.includes(doc.id) && <CheckCircle2 size={19} />}</span>
                                    </button>
                                    <button className="row-action" onClick={() => deleteDocument(doc.id)} title="Delete document"><Trash2 size={16} /></button>
                                </div>
                            );
                        })}
                    </div>
                    {processedDocuments.length > 0 && (
                        <button className="text-button select-all" onClick={() => setSelectedIds(selectedIds.length === processedDocuments.length ? [] : processedDocuments.map((doc) => doc.id))}>
                            {selectedIds.length === processedDocuments.length ? "Clear selection" : "Select all processed"}
                        </button>
                    )}
                </section>

                <section className="chat-panel panel">
                    <div className="panel-heading chat-heading">
                        <div><span className="section-kicker">02 · Ask</span><h2>{activeSession?.title || "New conversation"}</h2></div>
                        <span className="selection-label"><Sparkles size={15} /> {selectedIds.length} selected</span>
                    </div>
                    <div className="messages">
                        {messages.length === 0 && (
                            <div className="chat-empty"><span className="chat-orb"><Sparkles size={28} /></span><h3>What would you like to discover?</h3><p>Select one or more papers, then ask for a summary, comparison, methodology, or key finding.</p><div className="prompt-chips">{["Summarize the key findings", "Compare the methodologies", "What are the research gaps?"].map((prompt) => <button key={prompt} onClick={() => setQuestion(prompt)}>{prompt}<ChevronRight size={14} /></button>)}</div></div>
                        )}
                        {messages.map((message, index) => (
                            <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
                                <span className="message-avatar">{message.role === "assistant" ? <Bot size={17} /> : <UserRound size={17} />}</span>
                                <div><span className="message-role">{message.role === "assistant" ? "ResearchMind" : "You"}</span><p>{message.content}</p>{message.sources?.length > 0 && <div className="sources"><small>Sources</small>{message.sources.map((source, sourceIndex) => <span key={`${source.document_id}-${source.page_number}-${sourceIndex}`}><FileText size={12} /> {source.source} · p.{source.page_number}</span>)}</div>}</div>
                            </div>
                        ))}
                        {asking && <div className="message assistant"><span className="message-avatar"><Bot size={17} /></span><div><span className="message-role">ResearchMind</span><div className="typing"><i /><i /><i /></div></div></div>}
                        <div ref={messageEnd} />
                    </div>
                    <form className="composer" onSubmit={ask}>
                        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(e); } }} placeholder="Ask a question about your selected papers…" rows="2" />
                        <button disabled={asking || !question.trim()} title="Send question"><Send size={19} /></button>
                        <span>{selectedIds.length ? `Searching ${selectedIds.length} selected paper${selectedIds.length > 1 ? "s" : ""}` : "Select papers to begin"}</span>
                    </form>
                </section>

                <aside className="history-panel panel">
                    <div className="panel-heading"><div><span className="section-kicker">History</span><h2>Conversations</h2></div><button className="icon-button" onClick={startNewChat} title="New chat"><Plus size={18} /></button></div>
                    <div className="session-list">
                        {sessions.length === 0 && <div className="empty-small"><MessageSquare size={22} /><span>No conversations yet</span></div>}
                        {sessions.map((session) => <button className={`session-item ${activeSession?.id === session.id ? "active" : ""}`} key={session.id} onClick={() => openSession(session.id)}><MessageSquare size={16} /><span><strong>{session.title}</strong><small>{dateLabel(session.updated_at)}</small></span><i onClick={(event) => deleteSession(event, session.id)} title="Delete"><X size={14} /></i></button>)}
                    </div>
                </aside>
            </div>
            <Toast {...toast} onClose={() => setToast(null)} />
        </div>
    );
}
