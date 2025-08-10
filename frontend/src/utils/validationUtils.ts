// src/utils/validationUtils.ts

/**
 * Simple email regex
 */
export const isValidEmail = (email: string): boolean =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

/**
 * Checks if a string is a valid IP address
 */
export const isValidIP = (ip: string): boolean =>
    /^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(\d{1,3})){3}$/.test(ip);

/**
 * Checks for empty string or only whitespace
 */
export const isEmpty = (value: string): boolean => value.trim() === "";
