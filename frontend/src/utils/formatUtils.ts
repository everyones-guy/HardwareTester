// src/utils/formatUtils.ts

/**
 * Capitalizes the first letter of a word
 */
export const capitalize = (str: string) =>
    str.charAt(0).toUpperCase() + str.slice(1);

/**
 * Converts `snake_case` or `kebab-case` to `Title Case`
 */
export const toTitleCase = (str: string) =>
    str
        .replace(/[-_]/g, " ")
        .replace(/\b\w/g, (l) => l.toUpperCase());
