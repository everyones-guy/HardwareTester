// src/hooks/useLocalStorage.ts
import { useState } from "react";

/**
 * useLocalStorage Hook
 * Stores and retrieves a value from localStorage with reactivity.
 * @param key - The key used in localStorage.
 * @param initialValue - Default value if nothing is in localStorage.
 */
function useLocalStorage<T>(key: string, initialValue: T) {
    const [storedValue, setStoredValue] = useState<T>(() => {
        try {
            const item = window.localStorage.getItem(key);
            return item ? (JSON.parse(item) as T) : initialValue;
        } catch (error) {
            console.warn(`useLocalStorage: failed to read key "${key}"`, error);
            return initialValue;
        }
    });

    const setValue = (value: T | ((val: T) => T)) => {
        try {
            const valueToStore = value instanceof Function ? value(storedValue) : value;
            setStoredValue(valueToStore);
            window.localStorage.setItem(key, JSON.stringify(valueToStore));
        } catch (error) {
            console.error(`useLocalStorage: failed to set key "${key}"`, error);
        }
    };

    return [storedValue, setValue] as const;
}

export default useLocalStorage;
