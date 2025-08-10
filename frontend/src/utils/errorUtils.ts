// src/utils/errorUtils.ts

/**
 * Extracts a clean message from any error object
 */
export const extractErrorMessage = (err: unknown): string => {
    if (!err) return "Unknown error";

    if (typeof err === "string") return err;

    if (err instanceof Error) return err.message;

    if (typeof err === "object" && "message" in err) return String((err as any).message);

    return "Unhandled error format";
};

/**
 * Gracefully handles an error with toast and log
 */
export const handleError = (err: unknown, fallback = "An unexpected error occurred") => {
    const message = extractErrorMessage(err) || fallback;
    console.error("[UHT] Error:", err);
    // Optional: auto-toast
    import("react-toastify").then(({ toast }) => toast.error(message));
    return message;
};
