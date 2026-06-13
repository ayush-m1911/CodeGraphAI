/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0B0B',
        surface: '#1A1A1A',
        primary: {
          DEFAULT: '#D4AF37',
          hover: '#E6C15A',
        },
        text: {
          DEFAULT: '#F5F5F5',
          secondary: '#B0B0B0',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
