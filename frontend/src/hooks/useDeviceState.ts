// /src/hooks/useDeviceState.ts
import { useContext } from "react";
import { DeviceContext } from "@/context/DeviceContext";

const useDeviceState = () => {
    const context = useContext(DeviceContext);
    if (!context) throw new Error("useDeviceState must be used within a DeviceProvider");
    return context;
};

export default useDeviceState;