import axios from "axios";

const BASE_URL = "http://localhost:5000/api/mqtt";

export const connectMQTT = async () => {
    try {
        const response = await axios.post(`${BASE_URL}/connect`);
        return response.data || null;
    } catch (error) {
        console.error("Error connecting to MQTT:", error);
        return null;
    }
};

export const publishMessage = async (topic, payload) => {
    try {
        const response = await axios.post(`${BASE_URL}/publish`, { topic, payload });
        return response.data || null;
    } catch (error) {
        console.error(`Error publishing to topic ${topic}:`, error);
        return null;
    }
};
