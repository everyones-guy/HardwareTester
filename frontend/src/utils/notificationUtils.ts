// src/utils/notificationUtils.ts

import { toast } from "react-toastify";

/**
 * Shows a toast message based on type
 */
export const showToast = (
    message: string,
    type: "info" | "success" | "warning" | "error" = "info"
) => {
    switch (type) {
        case "success":
            toast.success(message);
            break;
        case "error":
            toast.error(message);
            break;
        case "warning":
            toast.warning(message);
            break;
        default:
            toast.info(message);
    }
};
