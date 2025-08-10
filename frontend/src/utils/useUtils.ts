// src/utils/useUtils.ts
import * as dateUtils from "./dateUtils";
import * as fileUtils from "./fileUtils";
import * as formatUtils from "./formatUtils";
import * as validationUtils from "./validationUtils";
import * as mqttUtils from "./mqttUtils";
import * as notificationUtils from "./notificationUtils";
import * as loggingUtils from "./loggingUtils";
import * as errorUtils from "./errorUtils";

export const useUtils = () => {
    return {
        ...dateUtils,
        ...fileUtils,
        ...formatUtils,
        ...validationUtils,
        ...mqttUtils,
        ...notificationUtils,
        ...loggingUtils,
        ...errorUtils,
    };
};
