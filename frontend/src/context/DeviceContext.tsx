import React, { createContext, useContext, useState, useEffect } from "react";
import { listDevices } from "@/services/hardwareService";

const DeviceContext = createContext(null);

export const DeviceProvider = ({ children }: { children: React.ReactNode }) => {
    const [devices, setDevices] = useState([]);
    const [loading, setLoading] = useState(true);

    const refreshDevices = async () => {
        setLoading(true);
        const data = await listDevices();
        setDevices(data || []);
        setLoading(false);
    };

    useEffect(() => {
        refreshDevices();
    }, []);

    return (
        <DeviceContext.Provider value={{ devices, refreshDevices, loading }}>
            {children}
        </DeviceContext.Provider>
    );
};

export const useDeviceContext = () => useContext(DeviceContext);
