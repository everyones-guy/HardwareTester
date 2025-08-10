// src/services/userService.ts
import APIService from "@/services/apiService";
import { APIResponse } from "@/types/apiTypes";

const BASE_PATH = "users";

const UserService = {
    /**
     * Fetch all registered users.
     */
    listUsers(): Promise<APIResponse<{ users: any[] }>> {
        return APIService.apiCallWithRetry(`${BASE_PATH}/list`, "GET", null, {}, 3);
    },

    /**
     * Add a new user.
     * @param userData - Basic user info
     */
    addUser(userData: { username: string; email: string; role: string }): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/add`, "POST", userData);
    },

    /**
     * Update user profile by ID.
     * @param id - User ID
     * @param data - Fields to update
     */
    updateUser(
        id: string,
        data: Partial<{ username: string; email: string; role: string }>
    ): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/update/${id}`, "POST", data);
    },

    /**
     * Delete user by ID.
     * @param id - User ID
     */
    deleteUser(id: string): Promise<APIResponse> {
        return APIService.apiCall(`${BASE_PATH}/delete/${id}`, "DELETE");
    },

    /**
     * Fetch single user details by ID.
     * @param id - User ID
     */
    getUserById(id: string): Promise<APIResponse<{ user: any }>> {
        return APIService.apiCall(`${BASE_PATH}/get/${id}`, "GET");
    },
};

export default UserService;
