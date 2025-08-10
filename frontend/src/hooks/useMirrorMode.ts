// src/hooks/useMirrorMode.ts
import { useState } from "react";
import EmulatorService from "@/services/emulatorApiService";

const useMirrorMode = () => {
    const [isMirroring, setIsMirroring] = useState(false);

    const toggleMirrorMode = async (deviceId: string) => {
        try {
            await EmulatorService.enableUIMirror(deviceId);
            setIsMirroring((prev) => !prev);
        } catch (error) {
            console.error("Failed to toggle mirror mode:", error);
        }
    };

    return { isMirroring, toggleMirrorMode };
};

export default useMirrorMode;
