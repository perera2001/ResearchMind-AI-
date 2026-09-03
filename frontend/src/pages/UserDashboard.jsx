import { Library } from "lucide-react";

import AppShell from "../components/AppShell";
import ResearchWorkspace from "../components/ResearchWorkspace";


export default function UserDashboard() {
    const navigation = [
        { id: "workspace", label: "Research workspace", icon: Library },
    ];

    return (
        <AppShell navigation={navigation} active="workspace" onNavigate={() => {}}>
            <ResearchWorkspace heading="Research workspace" />
        </AppShell>
    );
}
