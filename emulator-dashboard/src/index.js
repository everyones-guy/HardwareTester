import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import Dashboard from "./components/Dashboard"; // Load Dashboard directly

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
    <React.StrictMode>
        <Dashboard />
    </React.StrictMode>
);
