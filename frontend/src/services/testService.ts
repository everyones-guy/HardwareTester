// src/services/testService.ts
import APIService, { getWebSocketURL } from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";
import {
    TestPlan,
    TestResult,
    TestSchedule,
    TestExecutionStatus,
    TestLogUpdate,
} from "@/types/testTypes";

const BASE_PATH = "tests";

const TestService = {
    /**
     * Get all defined test plans.
     */
    getAllTestPlans(): Promise<APIResponse<{ plans: TestPlan[] }>> {
        return APIService.apiCall(`${BASE_PATH}/plans`, "GET");
    },

    /**
     * Execute a specific test plan on a device.
     * @param deviceId - Target device
     * @param planId - ID of the test plan
     */
    runTestPlan(deviceId: string, planId: string): Promise<APIResponse<TestExecutionStatus>> {
        return APIService.apiCall(`${BASE_PATH}/run`, "POST", { deviceId, planId });
    },

    /**
     * Abort a running test by ID.
     * @param testId - Active test execution ID
     */
    abortTest(testId: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/abort/${testId}`, "POST");
    },

    /**
     * Get test results globally or filtered by device.
     * @param deviceId - Optional filter by device
     */
    getTestResults(deviceId?: string): Promise<APIResponse<{ results: TestResult[] }>> {
        const endpoint = deviceId ? `${BASE_PATH}/results/${deviceId}` : `${BASE_PATH}/results`;
        return APIService.apiCall(endpoint, "GET");
    },

    /**
     * Schedule a test plan to run in the future.
     * @param schedule - Schedule metadata
     */
    scheduleTest(schedule: TestSchedule): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/schedule`, "POST", schedule);
    },

    /**
     * Delete a saved test plan.
     * @param planId - ID of the plan to delete
     */
    deleteTestPlan(planId: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/plans/${planId}`, "DELETE");
    },

    /**
     * Add or update a test plan.
     * @param plan - Complete test plan payload
     */
    saveTestPlan(plan: TestPlan): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/plans`, "POST", plan);
    },

    /**
     * Subscribe to live test logs over WebSocket.
     * @param testId - Active test execution ID
     * @param onUpdate - Callback for log data
     */
    subscribeToTestLogs(testId: string, onUpdate: (log: TestLogUpdate) => void): () => void {
        const socket = new WebSocket(getWebSocketURL(`${BASE_PATH}/logs/${testId}`));

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onUpdate(data);
            } catch (err) {
                console.error("Failed to parse test log:", err);
            }
        };

        socket.onerror = (err) => {
            console.error("WebSocket error (test logs):", err);
        };

        return () => socket.close();
    },
};

export default TestService;
