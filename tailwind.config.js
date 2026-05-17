/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        'lily-white': '#FFFFFF',
        'lily-cream': '#FDFCFB',
        'lily-gold': '#D4AF37',
        'lily-rose': '#F4EDE4',
        'lily-dark': '#1A1A1A',
        'lily-purple': '#B5441A',
        'lily-green': '#B8C5B0',
        'purple-dark': '#8E3313',
        'purple-light': 'rgba(181,68,26,0.15)',
        'gold-light': '#E5C158',
        terra: '#B5441A',
        'terra-dark': '#8E3313',
        gold: '#C9973A',
        ivory: '#FAF7F0',
        night: '#110D06',
        muted: '#7A6E63',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Playfair Display', 'Georgia', 'serif'],
      },
      fontSize: {
        xs:  ['0.75rem',   { lineHeight: '1.5' }],
        sm:  ['0.875rem',  { lineHeight: '1.5' }],
        base:['0.9375rem', { lineHeight: '1.6' }],
        lg:  ['1rem',      { lineHeight: '1.6' }],
        xl:  ['1.125rem',  { lineHeight: '1.5' }],
        '2xl':['1.25rem',  { lineHeight: '1.4' }],
        '3xl':['1.5rem',   { lineHeight: '1.3' }],
        '4xl':['2rem',     { lineHeight: '1.2' }],
      },
    },
  },
  plugins: [],
}
