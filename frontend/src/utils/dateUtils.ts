// src/utils/dateUtils.ts

/**
 * Format a date string or object to `YYYY-MM-DD HH:mm:ss`
 */
export const formatTimestamp = (input: string | Date): string => {
    const date = new Date(input);
    return date.toLocaleString(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
};

/**
 * Returns time difference between now and input (e.g., "5 minutes ago")
 */
export const timeAgo = (input: string | Date): string => {
    const now = new Date();
    const date = new Date(input);
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000); // in seconds

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
};
