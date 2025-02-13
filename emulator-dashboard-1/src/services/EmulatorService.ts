class EmulatorService {
    private isRunning: boolean = false;

    startEmulator(): void {
        if (!this.isRunning) {
            this.isRunning = true;
            console.log("Emulator started.");
        } else {
            console.log("Emulator is already running.");
        }
    }

    stopEmulator(): void {
        if (this.isRunning) {
            this.isRunning = false;
            console.log("Emulator stopped.");
        } else {
            console.log("Emulator is not running.");
        }
    }

    getStatus(): string {
        return this.isRunning ? "Emulator is running." : "Emulator is stopped.";
    }
}

export default EmulatorService;