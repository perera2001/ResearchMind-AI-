import { BrainCircuit } from "lucide-react";


export default function Brand({ compact = false }) {
    return (
        <div className={`brand ${compact ? "brand-compact" : ""}`}>
            <span className="brand-mark"><BrainCircuit size={22} /></span>
            <span>ResearchMind <b>AI</b></span>
        </div>
    );
}
