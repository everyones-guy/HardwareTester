// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "src"), // Allows @/services, @/components, etc.
        },
    },
    server: {
        port: 3000,
        strictPort: true,
        open: true,
        proxy: {
            "/api": {
                target: "http://localhost:5000/api", // Flask backend
                changeOrigin: true,
                secure: false,
            },
            "/socket.io": {
                target: "http://localhost:5000/api",
                ws: true,
            },
        },
    },
    build: {
        outDir: "build",
        sourcemap: true,
        emptyOutDir: true,
    },
});
