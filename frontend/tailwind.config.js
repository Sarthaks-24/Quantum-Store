/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#2563EB',
        'primary-hover': '#1D4ED8',
        'primary-light': '#EFF6FF',
        'primary-dark': '#1E40AF',
        'surface': '#F8FAFC',
        'card-bg': '#FFFFFF',
        'border-color': '#E2E8F0',
        'border-light': '#F1F5F9',
        'text-primary': '#0F172A',
        'text-secondary': '#475569',
        'text-muted': '#94A3B8',
      },
      borderRadius: {
        'sm': '8px',
        'md': '12px',
        'lg': '14px',
        'xl': '16px',
        '2xl': '20px',
      },
      boxShadow: {
        'card': '0 4px 20px rgba(0, 0, 0, 0.06)',
        'sm': '0 2px 8px rgba(0, 0, 0, 0.04)',
        'md': '0 4px 16px rgba(0, 0, 0, 0.08)',
        'lg': '0 8px 32px rgba(0, 0, 0, 0.12)',
      },
      backdropBlur: {
        'sm': '4px',
        'md': '8px',
      },
    },
  },
  plugins: [],
}
