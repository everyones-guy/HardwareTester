// /src/hooks/useTheme.ts
import { useEffect, useState } from "react";

const THEME_KEY = "preferred-theme";

const useTheme = () => {
    const [theme, setTheme] = useState<string>(() => {
        return localStorage.getItem(THEME_KEY) || "light";
    });

    useEffect(() => {
        document.body.setAttribute("data-theme", theme);
        localStorage.setItem(THEME_KEY, theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prev) => (prev === "light" ? "dark" : "light"));
    };

    return { theme, toggleTheme };
};

export default useTheme;