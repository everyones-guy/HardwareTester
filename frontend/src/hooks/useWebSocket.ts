// /src/hooks/useWebSocket.ts (additional useful hook)
import { useEffect, useRef } from "react";

const useWebSocket = (url: string, onMessage: (data: any) => void) => {
    const socketRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        socketRef.current = new WebSocket(url);

        socketRef.current.onmessage = (event) => {
            const parsedData = JSON.parse(event.data);
            onMessage(parsedData);
        };

        socketRef.current.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        return () => {
            socketRef.current?.close();
        };
    }, [url]);

    return socketRef;
};

export default useWebSocket;