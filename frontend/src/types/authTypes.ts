// src/types/authTypes.ts

/**
 * Payload for login credentials.
 */
export interface AuthCredentials {
    username: string;
    password: string;
}

/**
 * Payload for user registration.
 */
export interface RegistrationPayload {
    username: string;
    email: string;
    password: string;
    role?: string; // Optional: depends on your backend
}

/**
 * Response format from login or refresh endpoints.
 */
export interface AuthResponse {
    token: string;
    user?: {
        id: string;
        username: string;
        email?: string;
        role?: string;
        [key: string]: any; // Catch-all for backend fields
    };
}

/**
 * Minimal wrapper for token-only responses (refresh, etc.)
 */
export interface RefreshTokenResponse {
    token: string;
}
