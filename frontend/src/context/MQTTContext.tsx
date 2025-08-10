
// src/context/MQTTContext.tsx
import React, { createContext, useContext, useEffect, useState } from "react";
import {
    connectMQTT,
    disconnectMQTT,
    isMQTTConnected,
    publishMessage,
    subscribeToTopic,
    unsubscribeFromTopic,
} from "@/services/mqttService";

const MQTTContext = createContext(null);

export const MQTTProvider = ({ children }: { children: React.ReactNode }) => {
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        connectMQTT();
        setConnected(isMQTTConnected());

        return () => {
            disconnectMQTT();
        };
    }, []);

    return (
        <MQTTContext.Provider
            value={{ connected, publishMessage, subscribeToTopic, unsubscribeFromTopic }}>
            {children}
        </MQTTContext.Provider>
    );
};

export const useMQTTContext = () => useContext(MQTTContext);