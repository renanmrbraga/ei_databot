import react from "@vitejs/plugin-react-swc";
import path from "node:path";
import { defineConfig, loadEnv } from "vite";

// Com npm --prefix ./frontend ou Docker, o diretório atual é frontend/.
const frontendDir = process.cwd();
const projectRoot = path.resolve(frontendDir, "..");

export default defineConfig(({ mode }) => {
  // Ler somente esta variavel do .env da raiz; nunca carregar segredos no bundle.
  const env = loadEnv(mode, projectRoot, "API_PROXY_TARGET");
  const apiTarget = env.API_PROXY_TARGET || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    envDir: false,
    server: {
      host: "127.0.0.1",
      port: 8080,
      strictPort: true,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: { "@": path.resolve(frontendDir, "src") },
    },
  };
});
