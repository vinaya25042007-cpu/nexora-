/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1C2B2E",
        cream: "#F6F3EC",
        teal: { DEFAULT: "#12484B", light: "#1E6367" },
        sage: { DEFAULT: "#6FA98A", light: "#DCEBE2" },
        amber: { DEFAULT: "#E8A33D", light: "#FBEBD3" },
        coral: { DEFAULT: "#D64545", light: "#FBDEDE" },
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};