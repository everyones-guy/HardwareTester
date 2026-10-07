// vite.config.ts
//
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "node:path";
import { fileURLToPath } from "node:url";
import fs from 'node:fs';
import {createHash} from 'node:crypto';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const sourceHash=createHash('sha256');
function hashSource(directory:string){for(const entry of fs.readdirSync(directory,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))){const target=path.join(directory,entry.name);if(entry.isDirectory())hashSource(target);else sourceHash.update(path.relative(__dirname,target).split(path.sep).join('/')).update(fs.readFileSync(target));}}
hashSource(path.join(__dirname,'src'));
sourceHash.update(fs.readFileSync(path.join(__dirname,'package-lock.json')));

export default defineConfig({
  define:{__BUILD_INFO__:JSON.stringify({version:'0.4.0',build:process.env.VITE_BUILD_ID||sourceHash.digest('hex').slice(0,12),builtAt:new Date().toISOString()})},
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
            target: process.env.VITE_API_TARGET || "http://127.0.0.1:5000",
            changeOrigin: true,
            // DO NOT rewrite path. backend expects /api
        },
    },
},

  build: {
    outDir: "build",
    sourcemap: true,
    emptyOutDir: true,
  },
});
