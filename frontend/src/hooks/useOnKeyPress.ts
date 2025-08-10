// /src/hooks/useOnKeyPress.ts
import { useEffect } from "react";

const useOnKeyPress = (targetKey: string, handler: () => void) => {
    useEffect(() => {
        const keyListener = (event: KeyboardEvent) => {
            if (event.key === targetKey) handler();
        };

        window.addEventListener("keydown", keyListener);
        return () => window.removeEventListener("keydown", keyListener);
    }, [targetKey, handler]);
};

export default useOnKeyPress;