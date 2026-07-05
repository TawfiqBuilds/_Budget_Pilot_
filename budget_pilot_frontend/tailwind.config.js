/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Matches the existing Budget_Pilot app's warm "paper ledger" palette.
        paper: "#EFEBE0",
        card: "#FFFDF8",
        ink: "#242219",
        subink: "#6B6656",
        line: "#D3CBB5",
        turmeric: "#B9832A", // primary accent -- buttons, "add" actions
        clay: "#A24B3B",     // reserved for "over budget" / danger
        olive: "#5C7A4F",    // "on track" / positive states
      },
      fontFamily: {
        // System fonts, same stack as the existing app -- no webfont to load.
        display: ["Georgia", "'Iowan Old Style'", "'Times New Roman'", "serif"],
        sans: ["-apple-system", "'Segoe UI'", "Helvetica", "Arial", "sans-serif"],
        mono: ["'SFMono-Regular'", "Consolas", "'Liberation Mono'", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
}
