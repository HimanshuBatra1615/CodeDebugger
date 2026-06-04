/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:        '#070B14',
        surface:   '#0D1525',
        card:      '#111C30',
        border:    '#1A2840',
        accent:    '#22D3EE',
        'accent-dim': '#0891B2',
        't1':      '#E2E8F0',
        't2':      '#7C8FA8',
        't3':      '#3D5068',
        critical:  '#F43F5E',
        error:     '#FB923C',
        warning:   '#FBBF24',
        info:      '#38BDF8',
        success:   '#34D399',
      },
      fontFamily: {
        sans:    ['DM Sans', 'system-ui', 'sans-serif'],
        heading: ['Syne', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'fade-in':    'fadeIn 0.4s ease forwards',
        'slide-up':   'slideUp 0.35s ease forwards',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}
