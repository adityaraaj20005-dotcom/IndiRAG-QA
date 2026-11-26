import {defineConfig} from "vite";
import {resolve} from "node:path";
export default defineConfig({build:{rollupOptions:{input:Object.fromEntries(["index", "ask", "documents", "retrieval", "evaluation", "methodology", "about"].map(n=>[n,resolve(process.cwd(),n+".html")]))}}});
