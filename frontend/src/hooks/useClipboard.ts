// /src/hooks/useClipboard.ts
import { useState } from "react";

const useClipboard = (): [copy: (text: string) => void, copied: boolean] => {
    const [copied, setCopied] = useState(false);

    const copy = (text: string) => {
        navigator.clipboard.writeText(text).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        });
    };

    return [copy, copied];
};

export default useClipboard;