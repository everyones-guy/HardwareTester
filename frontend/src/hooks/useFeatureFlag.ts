// src/hooks/useFeatureFlag.ts
import { useState, useEffect } from "react";

const featureFlags = {
    enableExperimentalMetrics: false,
    showDebugTools: true,
    allowFirmwareDowngrade: false,
};

const useFeatureFlag = (flag: keyof typeof featureFlags) => {
    const [enabled, setEnabled] = useState<boolean>(false);

    useEffect(() => {
        setEnabled(!!featureFlags[flag]);
    }, [flag]);

    return enabled;
};

export default useFeatureFlag;
