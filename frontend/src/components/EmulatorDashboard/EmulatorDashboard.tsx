// src/components/EmulatorDashboard/EmulatorDashboard.tsx
import React from "react";
import EmulatorPanel from "./EmulatorPanel";
import ActiveEmulations from "./ActiveEmulations";
import "./EmulatorDashboard.css";
import "@/components/common/dashboard.css";


interface EmulatorDashboardProps {
    showActiveSidebar?: boolean;
}

/** Simple error boundary so a child panel crash won't blank the whole dashboard */
class PanelErrorBoundary extends React.Component<
    { title?: string; children: React.ReactNode },
    { hasError: boolean; msg?: string }
> {
    constructor(props: any) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(err: any) {
        return { hasError: true, msg: err?.message || "Something went wrong." };
    }
    componentDidCatch(error: any, info: any) {
        // eslint-disable-next-line no-console
        console.error("[EmulatorDashboard] Panel error:", error, info);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="panel-error">
                    <h3>{this.props.title || "Panel Error"}</h3>
                    <p>{this.state.msg}</p>
                    <button onClick={() => this.setState({ hasError: false, msg: undefined })}>
                        Retry render
                    </button>
                </div>
            );
        }
        return this.props.children as any;
    }
}

const EmulatorDashboard: React.FC = () => {
    return (
        <div className="emulator-dashboard">
            <div className="dashboard-header">
                <h2>Emulator</h2>
            </div>

            <div className="dashboard-grid cols-2">
                <section className="dashboard-section">
                    <EmulatorPanel />
                </section>
                <aside className="dashboard-section">
                    <ActiveEmulations />
                </aside>
            </div>
        </div>
    );
};

export default EmulatorDashboard;
