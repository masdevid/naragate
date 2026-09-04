/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Anton"', 'Impact', 'sans-serif'],
        body: ['"Geist"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        paper: {
          DEFAULT: 'oklch(14% 0.008 50)',
          2: 'oklch(18% 0.010 50)',
          3: 'oklch(22% 0.008 50)',
        },
        rule: 'oklch(28% 0.008 50)',
        ink: 'oklch(93% 0.006 70)',
        muted: 'oklch(60% 0.006 50)',
        dim: 'oklch(42% 0.006 50)',
        accent: {
          DEFAULT: 'oklch(62% 0.22 35)',
          dim: 'oklch(50% 0.18 35)',
        },
      },
    },
  },
  plugins: [],
};
