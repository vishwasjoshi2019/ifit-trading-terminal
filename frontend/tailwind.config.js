/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#080a0c',
          panel: '#0e1116',
          border: '#1a1f26',
          header: '#141820',
          hover: '#1b222c',
          text: '#d1d5db',
          muted: '#6b7280',
          green: '#22c55e',
          red: '#ef4444',
          amber: '#f59e0b',
          blue: '#3b82f6',
        }
      },
      fontFamily: {
        mono: ['SF Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
