export interface EmulatorStatus {
    isRunning: boolean;
    error?: string;
    lastStarted?: Date;
}

export interface DashboardProps {
    status: EmulatorStatus;
    onStart: () => void;
    onStop: () => void;
}