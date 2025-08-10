// /src/hooks/useAuth.ts
import { useEffect, useState } from "react";
import { getUserProfile, refreshAuthToken } from "@/services/apiService";

const useAuth = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUser = async () => {
            const token = await refreshAuthToken();
            if (!token) return setLoading(false);

            const profile = await getUserProfile();
            setUser(profile);
            setLoading(false);
        };

        fetchUser();
    }, []);

    return { user, loading };
};

export default useAuth;