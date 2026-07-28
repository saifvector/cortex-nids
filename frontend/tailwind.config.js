/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          bg: '#04070E',
          card: 'rgba(13, 20, 36, 0.6)',
          panel: '#0B1220',
          border: 'rgba(255, 255, 255, 0.12)',
          borderHover: 'rgba(255, 255, 255, 0.25)',
          blue: '#3B82F6',
          cyan: '#22D3EE',
          purple: '#8B5CF6',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#F43F5E',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Space Grotesk', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
