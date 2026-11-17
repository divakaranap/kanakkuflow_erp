/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC",
        card: "#FFFFFF",
        primaryText: "#172033",
        secondaryText: "#64748B",
        accent: "#2563EB",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        border: "#E2E8F0",
      },
    },
  },
  plugins: [],
}
