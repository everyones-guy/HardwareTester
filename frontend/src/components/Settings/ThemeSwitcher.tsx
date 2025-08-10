import React, { useEffect, useState } from "react";
import "./ThemeSwitcher.css";

const ThemeSwitcher: React.FC = () => {
    const [theme, setTheme] = useState<"light" | "dark">("light");

    useEffect(() => {
        const stored = localStorage.getItem("theme");
        if (stored === "dark") {
            setTheme("dark");
            document.body.classList.add("dark-theme");
        }
    }, []);

    const toggleTheme = () => {
        const newTheme = theme === "light" ? "dark" : "light";
        setTheme(newTheme);

        if (newTheme === "dark") {
            document.body.classList.add("dark-theme");
        } else {
            document.body.classList.remove("dark-theme");
        }

        localStorage.setItem("theme", newTheme);
    };

    return (
        <div className="theme-switcher">
            <h3>Theme</h3>
            <button onClick={toggleTheme}>
                Switch to {theme === "light" ? "Dark" : "Light"} Mode
            </button>
        </div>
    );
};

export default ThemeSwitcher;
