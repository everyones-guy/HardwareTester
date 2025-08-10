// src/App.tsx
import React from "react";
import AppRoutes from "./routes/AppRoutes";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const App: React.FC = () => (
    <>
        <AppRoutes />
        <ToastContainer position="top-right" autoClose={5000} hideProgressBar />
    </>
);

export default App;
