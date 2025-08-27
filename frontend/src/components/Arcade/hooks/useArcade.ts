// File: src/components/Arcade/hooks/useArcade.ts
import { useEffect } from "react";
import { initArcadeIntegrations } from "@/components/Arcade/integrations/ArcadeIntegrations";

export default function useArcade() {
    useEffect(() => {
        initArcadeIntegrations();
    }, []);
}