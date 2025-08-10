// src/types/userTypes.ts

export interface User {
    id: string;
    username: string;
    email: string;
    role: "Admin" | "Tester" | "Viewer";
    isActive: boolean;
    createdAt: string;
    lastLogin?: string;
}

export interface Session {
    id: string;
    userId: string;
    sessionId: string;
    loginTime: string;
    logoutTime?: string;
    ipAddress?: string;
    deviceInfo?: string;

}

export interface UserProfile {
    id: string;
    username: string;
    email: string;
    role: string;
    avatarUrl?: string;
    createdAt?: string;
}