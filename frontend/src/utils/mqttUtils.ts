// src/utils/mqttUtils.ts

import { MqttClient, IClientOptions } from "mqtt";

/**
 * Safely builds an MQTT command payload.
 * @param action - The MQTT action string (e.g., 'navigate', 'activate').
 * @param parameters - Optional key-value parameter object.
 * @returns JSON stringified MQTT payload.
 */
export const buildMQTTCommand = (
    action: string,
    parameters: Record<string, any> = {}
): string => {
    return JSON.stringify({ action, ...parameters });
};

/**
 * Shortens long MQTT topic names to only show the last few segments.
 * @param topic - Full MQTT topic string (e.g., "machine/xyz/controller/peripheral").
 * @param maxParts - Maximum number of trailing parts to include.
 * @returns Shortened MQTT topic string.
 */
export const shortenTopic = (topic: string, maxParts: number = 3): string => {
    const parts = topic.split("/");
    if (parts.length <= maxParts) return topic;
    return `.../${parts.slice(-maxParts).join("/")}`;
};

/**
 * Attempts to reconnect an MQTT client if it's not connected.
 * @param client - MQTT.js client instance.
 * @param options - Optional MQTT connection options.
 */
export const reconnectMQTT = (
    client: MqttClient,
    options?: IClientOptions
): void => {
    if (!client.connected) client.reconnect(options);
};
