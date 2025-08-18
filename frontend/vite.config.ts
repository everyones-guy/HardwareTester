// vite.config.ts
//
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(), // if you're using paths like "@/components/..."; safe to keep even if unused
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
// vite.config.ts
server: {
    proxy: {
        "/api": {
            target: "http://127.0.0.1:5000",
            changeOrigin: true,
            // DO NOT rewrite path — backend expects /api
        },
    },
},

  build: {
    outDir: "build",
    sourcemap: true,
    emptyOutDir: true,
  },
});
