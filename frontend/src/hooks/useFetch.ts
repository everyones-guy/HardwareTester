// /src/hooks/useFetch.ts
import { useEffect, useState } from "react";
import axios, { AxiosRequestConfig } from "axios";

const useFetch = <T>(url: string, config: AxiosRequestConfig = {}) => {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.get<T>(url, config);
                setData(response.data);
            } catch (err) {
                console.error(err);
                setError("Failed to fetch data.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [url]);

    return { data, loading, error };
};

export default useFetch;