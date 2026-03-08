import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        border: "#e5e7eb",
        surface: "#ffffff",
        muted: "#f8fafc",
        text: "#111827",
        subtext: "#6b7280"
      }
    }
  },
  plugins: []
};

export default config;
