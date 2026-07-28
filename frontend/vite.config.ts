import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const viewerPath = resolve(__dirname, "../src/rigorgraph/viewer/index.html");

export default defineConfig({
  plugins: [
    react(),
    viteSingleFile(),
    {
      name: "normalize-viewer-line-endings",
      closeBundle() {
        const content = readFileSync(viewerPath, "utf8");
        const normalized = content
          .replace(/\r\n?/g, "\n")
          .replace('<div id="root"></div>\n\n  </body>', '<div id="root"></div>\n  </body>');
        writeFileSync(viewerPath, normalized, "utf8");
      },
    },
  ],
  base: "./",
  build: {
    outDir: resolve(__dirname, "../src/rigorgraph/viewer"),
    emptyOutDir: true,
    cssCodeSplit: false,
    assetsInlineLimit: 100000000,
    rollupOptions: {
      output: { inlineDynamicImports: true },
    },
  },
});
