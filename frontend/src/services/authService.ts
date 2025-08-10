// src/services/authService.ts
import APIService from "@/services/apiService";
import {
    AuthCredentials,
    AuthResponse,
    RegistrationPayload,
} from "@/types/authTypes";
import {
    setToken,
    clearToken,
} from "@/utils/tokenUtils";

const BASE_PATH = "auth";

const AuthService = {
    /**
     * Log in and store the returned token.
     * @param credentials - User credentials
     * @returns AuthResponse with token and optional user info
     */
    async login(credentials: AuthCredentials): Promise<AuthResponse> {
        const res = await APIService.apiCall<AuthResponse>(
            `${BASE_PATH}/login`,
            "POST",
            credentials
        );
        if (res.token) setToken(res.token);
        return res;
    },

    /**
     * Log out by clearing the stored token.
     */
    logout(): void {
        clearToken();
        // Optionally return APIService.apiCall(`${BASE_PATH}/logout`, "POST");
    },

    /**
     * Register a new user account.
     * @param userData - User registration details
     * @returns Raw backend response
     */
    async register(userData: RegistrationPayload): Promise<any> {
        return APIService.apiCall(`${BASE_PATH}/register`, "POST", userData);
    },

    /**
     * Refresh and store a new token from the server.
     * @returns Object containing the new token
     */
    async refreshToken(): Promise<{ token: string }> {
        const res = await APIService.apiCall<AuthResponse>(
            `${BASE_PATH}/refresh-token`,
            "POST"
        );
        if (res.token) setToken(res.token);
        return { token: res.token };
    },
};

export default AuthService;
