/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#e15c46', // Heron signature vermilion / orange
          dark: '#c44834',
          light: '#ff735c',
        },
        bg: {
          DEFAULT: '#ecece4', // Heron retro CAD canvas warm gray/bone
          subtle: '#e2e2d8',
          card: '#f4f4ec',
          dark: '#1c1c1b',
        },
        border: {
          cad: '#282828',
          subtle: '#28282833',
        },
        primary: '#282828',
        secondary: '#5c5c56',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Space Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
