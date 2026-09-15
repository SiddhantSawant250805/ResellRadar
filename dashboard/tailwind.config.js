/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f131c',
        surface: {
          DEFAULT: '#0f131c',
          lowest: '#0a0e16',
          low: '#181c24',
          container: '#1c2028',
          high: '#262a33',
          highest: '#31353e',
        },
        primary: {
          DEFAULT: '#4cd7f6',
          container: '#06b6d4',
          dim: '#acedff',
        },
        secondary: {
          DEFAULT: '#4edea3',
          container: '#00a572',
        },
        tertiary: {
          DEFAULT: '#c0c1ff',
          container: '#6366f1',
        },
        accent: {
          amber: '#f59e0b',
          crimson: '#ef4444',
        },
        outline: {
          DEFAULT: '#869397',
          variant: '#3d494c',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
