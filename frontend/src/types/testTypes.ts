// src/types/testTypes.ts

export interface TestPlan {
    id: string;
    name: string;
    description?: string;
    steps: TestStep[];
    createdBy?: string;
    createdAt?: string;
    updatedAt?: string;
}

export interface TestStep {
    name: string;
    action: string;
    expectedResult?: string;
    parameters?: Record<string, any>;
}

export interface TestSchedule {
    deviceId: string;
    planId: string;
    scheduledTime: string; // ISO timestamp
}

export interface TestExecutionStatus {
    testId: string;
    status: "started" | "queued" | "completed" | "aborted" | "failed";
    startTime?: string;
    endTime?: string;
}

export interface TestResult {
    testId: string;
    deviceId: string;
    planId: string;
    status: "passed" | "failed" | "aborted";
    logs: string[];
    executedAt: string;
}

export interface TestLogUpdate {
    testId: string;
    timestamp: string;
    message: string;
    level?: "info" | "warn" | "error";
}
