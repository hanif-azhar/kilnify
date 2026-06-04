import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy all /api requests to the FastAPI backend on port 8003.
export default defineConfig({
  plugins: [react()],
  resolve: {
    // shadcn/ui components import via the "@/..." alias.
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8003",
        changeOrigin: true,
      },
    },
  },
});
