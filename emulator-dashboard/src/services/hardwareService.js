import axios from "axios";

const BASE_URL = "http://localhost:5000/api/hardware";

export const listDevices = async () => {
    try {
        const response = await axios.get(`${BASE_URL}/list`);
        return response.data.devices || [];
    } catch (error) {
        console.error("Error fetching devices:", error);
        return [];
    }
};

export const getDeviceDetails = async (deviceId) => {
    try {
        const response = await axios.get(`${BASE_URL}/device/${deviceId}`);
        return response.data.device || null;
    } catch (error) {
        console.error(`Error fetching details for device ${deviceId}:`, error);
        return null;
    }
};
