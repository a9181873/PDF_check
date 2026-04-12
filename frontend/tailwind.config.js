/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // CTBC Brand Colors
        primary: {
          50: "#e6f7ec",
          100: "#c2ecd3",
          200: "#9ce0b8",
          300: "#75d49d",
          400: "#4fc882",
          500: "#009944", // CTBC Green
          600: "#007a36",
          700: "#005c28",
          800: "#003d1b",
          900: "#001f0d",
        },
        accent: {
          50: "#fde8e9",
          100: "#f9c0c3",
          200: "#f5979c",
          300: "#f16f76",
          400: "#ed4650",
          500: "#E60012", // CTBC Red
          600: "#b8000e",
          700: "#8a000b",
          800: "#5c0007",
          900: "#2e0004",
        },
        // Neutral grayscale
        gray: {
          50: "#fafafa",
          100: "#f5f5f5",
          200: "#eeeeee",
          300: "#e0e0e0",
          400: "#bdbdbd",
          500: "#9e9e9e",
          600: "#757575",
          700: "#616161",
          800: "#424242",
          900: "#333333", // Text color
        },
        // Diff colors - functional but harmonized with brand
        diff: {
          added: "#009944", // CTBC Green for added content
          deleted: "#E60012", // CTBC Red for deleted content
          modified: "#ff9800", // Orange for modifications
          text: "#673ab7", // Purple for text changes
          highlight: "#ffeb3b", // Yellow for highlights
        },
        // Status colors aligned with diff colors
        status: {
          confirmed: "#009944", // CTBC Green
          flagged: "#E60012", // CTBC Red
          pending: "#ff9800", // Orange
          missing: "#9e9e9e", // Gray
        },
      },
      fontFamily: {
        sans: ["Noto Sans TC", "Segoe UI", "PingFang TC", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        "soft": "0 2px 4px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)",
        "medium": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        "large": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-subtle": "pulseSubtle 2s infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.8" },
        },
      },
    },
  },
  plugins: [],
}
