import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "#f6f1ea",
        ink: "#111827",
        muted: "#6b7280",
        panel: "#fffaf4",
        accent: "#0f766e",
        accentSoft: "#ccfbf1",
      },
      boxShadow: {
        glow: "0 24px 80px rgba(15, 118, 110, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
