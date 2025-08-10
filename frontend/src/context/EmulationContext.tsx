// src/context/EmulationContext.tsx
import React, { createContext, useContext, useState } from "react";

const EmulationContext = createContext(null);

export const EmulationProvider = ({ children }: { children: React.ReactNode }) => {
    const [activeEmulation, setActiveEmulation] = useState(null);

    return (
        <EmulationContext.Provider value={{ activeEmulation, setActiveEmulation }}>
            {children}
        </EmulationContext.Provider>
    );
};

export const useEmulationContext = () => useContext(EmulationContext);