import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        deepNavy: "#071527",
        navy: "#0F172A",
        teal: "#0F766E",
        softTeal: "#5EEAD4",
        organic: "#65A30D",
        leaf: "#84CC16",
        cream: "#F8F5EC",
        mist: "#ECFEFF",
        softSky: "#E0F2FE",
        sky: "#38BDF8",
        gold: "#FACC15",
        softGray: "#E5E7EB"
      },
      fontFamily: {
        sans: ["Inter", "Manrope", "system-ui", "sans-serif"],
        display: ["Manrope", "Inter", "system-ui", "sans-serif"]
      },
      boxShadow: {
        organic: "0 24px 80px rgba(15, 118, 110, 0.16)",
        glow: "0 0 42px rgba(94, 234, 212, 0.36)"
      }
    }
  },
  plugins: []
} satisfies Config;
