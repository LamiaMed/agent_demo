import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        page: "#eef5fb",
        ink: "#0f172a",
        muted: "#5b7083",
        panel: "#ffffff",
        accent: "#0f7490",
        accentSoft: "#d9f3fb",
        clinic: "#1f6f8b",
        clinicDark: "#0b2a3d",
        clinicMint: "#dff7f5",
      },
      boxShadow: {
        glow: "0 24px 80px rgba(15, 116, 144, 0.16)",
      },
    },
  },
  plugins: [],
};

export default config;
