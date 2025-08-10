// src/hooks/useSessionStorage.ts
import { useState } from "react";

function useSessionStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
    const storedValue = sessionStorage.getItem(key);
    const [value, setValue] = useState<T>(
        storedValue ? JSON.parse(storedValue) : initialValue
    );

    const setStoredValue = (newValue: T) => {
        setValue(newValue);
        sessionStorage.setItem(key, JSON.stringify(newValue));
    };

    return [value, setStoredValue];
}

export default useSessionStorage;
