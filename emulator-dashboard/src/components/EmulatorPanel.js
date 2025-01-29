import React, { useState, useEffect } from "react";
import { useRef } from "react";
import axios from "axios";

const EmulatorPanel = () => {
    // State hooks
    const [osType, setOsType] = useState("linux"); // Default OS
    const [firmware, setFirmware] = useState(null);
    const [firmwareError, setFirmwareError] = useState(null);
    const [isTouchscreenEmulated, setIsTouchscreenEmulated] = useState(false);
    const [isMirrorEnabled, setIsMirrorEnabled] = useState(false);
    const [scheduledEvents, setScheduledEvents] = useState([]);
    const [isEmulationRunning, setIsEmulationRunning] = useState(false);
    const [uiScanResults, setUiScanResults] = useState(null);

    // Refs for live events or updates
    const eventTimeouts = useRef([]);

    // Sample configurations
    const osOptions = ["linux", "windows", "raspberryPi", "unknown"];

    // Firmware Integrity Check - Simulated function
    const checkFirmwareIntegrity = async (firmwareFile) => {
        try {
            const response = await axios.post("/api/firmware/validate", {
                firmwareFile,
            });
            setFirmwareError(null);
            setUiScanResults(response.data.uiScanResults);
        } catch (error) {
            setFirmwareError("Firmware integrity check failed.");
        }
    };

    // Handle OS Change
    const handleOsChange = (e) => {
        setOsType(e.target.value);
    };

    // Start/Stop Emulation
    const toggleEmulation = () => {
        setIsEmulationRunning((prev) => !prev);
    };

    // Handle touch screen emulation
    const handleTouchscreenEmulation = () => {
        setIsTouchscreenEmulated(!isTouchscreenEmulated);
    };

    // Handle mirror toggle for bidirectional communication
    const handleMirrorToggle = () => {
        setIsMirrorEnabled(!isMirrorEnabled);
    };

    // Schedule Events
    const scheduleEvent = (event) => {
        const eventId = setTimeout(() => {
            event();
        }, event.delay);
        eventTimeouts.current.push(eventId);
        setScheduledEvents((prevEvents) => [...prevEvents, event]);
    };

    const cancelScheduledEvents = () => {
        eventTimeouts.current.forEach((timeoutId) => clearTimeout(timeoutId));
        setScheduledEvents([]);
    };

    // Render Scheduled Events
    const renderScheduledEvents = () => {
        return scheduledEvents.map((event, index) => (
            <div key={index}>
                <p>Event: {event.name}</p>
                <p>Scheduled for: {event.delay}ms</p>
            </div>
        ));
    };

    return (
        <div className="emulator-panel">
            <h1>Advanced Emulator Panel</h1>
            <div>
                <label>Select OS Type: </label>
                <select value={osType} onChange={handleOsChange}>
                    {osOptions.map((os, index) => (
                        <option key={index} value={os}>
                            {os.charAt(0).toUpperCase() + os.slice(1)}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label>Upload Firmware:</label>
                <input
                    type="file"
                    accept=".bin,.hex,.img"
                    onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) {
                            setFirmware(file);
                            checkFirmwareIntegrity(file);
                        }
                    }}
                />
            </div>

            {firmwareError && <p className="error">{firmwareError}</p>}

            <div>
                <button onClick={toggleEmulation}>
                    {isEmulationRunning ? "Stop Emulation" : "Start Emulation"}
                </button>
            </div>

            <div>
                <label>
                    <input
                        type="checkbox"
                        checked={isTouchscreenEmulated}
                        onChange={handleTouchscreenEmulation}
                    />
                    Emulate Touchscreen Controller
                </label>
                <br />
                <label>
                    <input
                        type="checkbox"
                        checked={isMirrorEnabled}
                        onChange={handleMirrorToggle}
                    />
                    Enable Mirror (Bidirectional Communication)
                </label>
            </div>

            <div>
                <h3>Scheduled Events</h3>
                {renderScheduledEvents()}
            </div>

            <div>
                <h3>UI Scan Results</h3>
                {uiScanResults && (
                    <div>
                        <p>User Interfaces Found:</p>
                        <pre>{JSON.stringify(uiScanResults, null, 2)}</pre>
                    </div>
                )}
            </div>

            <div>
                <button
                    onClick={() =>
                        scheduleEvent({
                            name: "Power Cycle",
                            delay: 5000,
                            event: () => alert("Emulating power cycle..."),
                        })
                    }
                >
                    Schedule Power Cycle Event (5s)
                </button>

                <button onClick={cancelScheduledEvents}>Cancel Scheduled Events</button>
            </div>
        </div>
    );
};

export default EmulatorPanel;
