// /src/hooks/useMQTT.ts
import { useEffect, useState } from "react";
import {
    connectMQTT,
    disconnectMQTT,
    subscribeToTopic,
    unsubscribeFromTopic,
    publishMessage,
    isMQTTConnected
} from "@/services/mqttService";

const useMQTT = (topic: string, onMessage: (msg: string) => void) => {
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        connectMQTT();
        setConnected(isMQTTConnected());
        subscribeToTopic(topic, onMessage);

        return () => {
            unsubscribeFromTopic(topic);
            disconnectMQTT();
        };
    }, [topic]);

    const sendMessage = (message: string) => publishMessage(topic, message);

    return { connected, sendMessage };
};

export default useMQTT;