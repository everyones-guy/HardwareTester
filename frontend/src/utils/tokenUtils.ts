// /src/utils/tokenUtils.ts
const AUTH_TOKEN_KEY = "authToken";

/**
 * Retrieve token from session storage
 */
export const getToken = (): string | null =>
    sessionStorage.getItem(AUTH_TOKEN_KEY);

/**
 * Save token to session storage
 */
export const setToken = (token: string): void =>
    sessionStorage.setItem(AUTH_TOKEN_KEY, token);

/**
 * Clear token from session storage
 */
export const clearToken = (): void =>
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
