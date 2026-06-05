/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        // OEMPartner brand colors
        'OEMPartner-blue': '#0033A0',
        'OEMPartner-red': '#E60012',
        'OEMPartner-blue-light': '#1a4db8',
        'OEMPartner-blue-dark': '#002280',
      },
    },
  },
  plugins: [],
}
