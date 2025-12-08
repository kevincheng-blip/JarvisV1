import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // J-GOD PRO 色系
        "ultra-dark": "#0C0F11",
        "titanium": "#1A1F24",
        "ai-blue": "#0099FF",
        "military-green": "#00FFBF",
        "command-red": "#FF4D4D",
        "metal-gold": "#D2B48C",
      },
      boxShadow: {
        "glow-blue": "0 0 20px rgba(0, 153, 255, 0.5)",
        "glow-green": "0 0 20px rgba(0, 255, 191, 0.5)",
        "glow-red": "0 0 20px rgba(255, 77, 77, 0.5)",
        "glow-gold": "0 0 20px rgba(210, 180, 140, 0.5)",
        "glow-strong-blue": "0 0 40px rgba(0, 153, 255, 0.8)",
        "glow-strong-green": "0 0 40px rgba(0, 255, 191, 0.8)",
      },
      animation: {
        "pulse-border": "pulse-border 2s ease-in-out infinite",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "typing": "typing 0.3s ease-in",
        "shimmer": "shimmer 2s infinite",
      },
      keyframes: {
        "pulse-border": {
          "0%, 100%": { "box-shadow": "0 0 20px rgba(0, 153, 255, 0.3)" },
          "50%": { "box-shadow": "0 0 40px rgba(0, 153, 255, 0.6)" },
        },
        "glow-pulse": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        typing: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
export default config;

