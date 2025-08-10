// src/context/UserContext.tsx
import React, { createContext, useContext, useEffect, useState } from "react";
import { getUserProfile } from "@/services/apiService";
import { UserProfile } from "@/types/userTypes";

interface UserContextType {
    user: UserProfile | null;
    setUser: React.Dispatch<React.SetStateAction<UserProfile | null>>;
    loading: boolean;
}

const UserContext = createContext<UserContextType | null>(null);

export const UserProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            const profile = await getUserProfile();
            setUser(profile);
            setLoading(false);
        })();
    }, []);

    return (
        <UserContext.Provider value={{ user, setUser, loading }}>
            {children}
        </UserContext.Provider>
    );
};

export const useUserContext = (): UserContextType => {
    const context = useContext(UserContext);
    if (!context) throw new Error("useUserContext must be used within a UserProvider");
    return context;
};