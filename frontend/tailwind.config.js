/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-gradient-start': '#0f172a',
        'bg-gradient-end': '#071033',
        'accent-indigo': '#7c3aed',
        'accent-teal': '#06b6d4',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glow-indigo': '0 0 20px rgba(124, 58, 237, 0.5)',
        'glow-teal': '0 0 20px rgba(6, 182, 212, 0.5)',
      },
      backdropBlur: {
        'glass': '4px',
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(135deg, #0f172a 0%, #071033 100%)',
      }
    },
  },
  plugins: [],
}
