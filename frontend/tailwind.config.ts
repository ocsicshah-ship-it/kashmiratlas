import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        panel: "#0f1720",
        panelMuted: "#1b2733",
      },
    },
  },
  plugins: [],
} satisfies Config;
