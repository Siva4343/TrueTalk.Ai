/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'teams': {
                    purple: '#6264A7',
                    dark: '#292929',
                    darker: '#1F1F1F',
                    light: '#F3F2F1',
                    border: '#3B3A39',
                    hover: '#3B3B3B',
                }
            },
        },
    },
    plugins: [],
}
