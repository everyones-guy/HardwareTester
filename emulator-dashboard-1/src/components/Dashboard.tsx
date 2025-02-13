import React, { useEffect, useState } from "react"; // Import React and hooks
import { EmulatorService } from "../services/EmulatorService"; // Import EmulatorService
import { EmulatorStatus } from '../types'; // Import EmulatorStatus type

const Dashboard: React.FC = () => {
    const [status, setStatus] = useState<EmulatorStatus | null>(null); // State to hold emulator status
    const emulatorService = new EmulatorService(); // Instantiate EmulatorService

    useEffect(() => {
        const fetchStatus = async () => {
            const currentStatus = await emulatorService.getStatus(); // Fetch current status
            setStatus(currentStatus); // Update state with current status
        };

        fetchStatus(); // Call fetchStatus on component mount
    }, []); // Empty dependency array means this runs once on mount

    const handleStart = async () => {
        await emulatorService.start(); // Start the emulator
        const currentStatus = await emulatorService.getStatus(); // Fetch updated status
        setStatus(currentStatus); // Update state with new status
    };

    const handleStop = async () => {
        await emulatorService.stop(); // Stop the emulator
        const currentStatus = await emulatorService.getStatus(); // Fetch updated status
        setStatus(currentStatus); // Update state with new status
    };

    return (
        <div>
            <h1>Emulator Dashboard</h1>
            {status && (
                <div>
                    <p>Status: {status.state}</p> {/* Display current status */}
                    <button onClick={handleStart}>Start Emulator</button> {/* Button to start emulator */}
                    <button onClick={handleStop}>Stop Emulator</button> {/* Button to stop emulator */}
                </div>
            )}
        </div>
    );
};

export default Dashboard; // Export Dashboard component