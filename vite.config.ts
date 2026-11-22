import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Hasil build adalah file statis di dist/. Bisa di-deploy ke Vercel atau diunggah ke cPanel.
export default defineConfig({
  plugins: [react()],
});
