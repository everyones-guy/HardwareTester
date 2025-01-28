import axios from "axios";

const BASE_URL = "http://localhost:5000/api/emulators";

export const listEmulations = async () => {
    try {
        const response = await axios.get(`${BASE_URL}/list`);
        return response.data || [];
    } catch (error) {
        console.error("Error fetching emulations:", error);
        return [];
    }
};

export const startEmulation = async (emulationData) => {
    try {
        const response = await axios.post(`${BASE_URL}/start`, emulationData);
        return response.data || null;
    } catch (error) {
        console.error("Error starting emulation:", error);
        return null;
    }
};
