// src/utils/loggingUtils.ts

/**
 * Logs a message to the console with a consistent prefix.
 */
export const logInfo = (message: string, context?: any) => {
    console.log(`[UHT] ${message}`, context || "");
};

export const logWarn = (message: string, context?: any) => {
    console.warn(`[UHT] ${message}`, context || "");
};

export const logError = (message: string, context?: any) => {
    console.error(`[UHT] ${message}`, context || "");
};

/**
 * Tracks a timed operation, logs duration when done
 */
export const logTimer = (label: string): (() => void) => {
    const start = performance.now();
    return () => {
        const duration = (performance.now() - start).toFixed(2);
        console.log(`[UHT] ${label} took ${duration}ms`);
    };
};
