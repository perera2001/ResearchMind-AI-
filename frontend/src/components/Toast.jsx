import { AlertCircle, CheckCircle2, X } from "lucide-react";


export default function Toast({ message, type = "success", onClose }) {
    if (!message) return null;

    return (
        <div className={`toast toast-${type}`} role="status">
            {type === "error"
                ? <AlertCircle size={19} />
                : <CheckCircle2 size={19} />}
            <span>{message}</span>
            <button type="button" onClick={onClose} aria-label="Close notification">
                <X size={16} />
            </button>
        </div>
    );
}
