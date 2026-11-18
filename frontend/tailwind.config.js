/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primaryPurple: "#7655E8",
        secondaryPurple: "#9675F5",
        lightLavender: "#F2EEFF",
        lavenderBg: "#F8F7FC",
        mainBg: "#FAFAFD",
        cardBg: "#FFFFFF",
        primaryText: "#17152B",
        secondaryText: "#77758A",
        borderSubtle: "#EAE8F1",
        success: "#16A36A",
        warning: "#E9A23B",
        danger: "#E05252",
        info: "#4385E8",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(23, 21, 43, 0.03), 0 4px 16px 0 rgba(118, 85, 232, 0.04)",
        cardHover: "0 4px 12px 0 rgba(23, 21, 43, 0.05), 0 8px 24px 0 rgba(118, 85, 232, 0.08)",
        dropdown: "0 10px 30px 0 rgba(23, 21, 43, 0.08), 0 4px 12px 0 rgba(118, 85, 232, 0.04)",
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
