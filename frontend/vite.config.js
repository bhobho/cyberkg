import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: ["ec2-3-81-6-27.compute-1.amazonaws.com"],
    proxy: {
      "/api": "http://localhost:8001",
    },
  },
});
