import axios from "axios";

const BASE_URL = "http://localhost:5000/api/serial";

export const connectSerial = async (port, baudrate) => {
    try {
        const response = await axios.post(`${BASE_URL}/connect`, { port, baudrate });
        return response.data || null;
    } catch (error) {
        console.error(`Error connecting to serial port ${port}:`, error);
        return null;
    }
};

export const sendSerialData = async (data) => {
    try {
        const response = await axios.post(`${BASE_URL}/send`, { data });
        return response.data || null;
    } catch (error) {
        console.error("Error sending serial data:", error);
        return null;
    }
};
