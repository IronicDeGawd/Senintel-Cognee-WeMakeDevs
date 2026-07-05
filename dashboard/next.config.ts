import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloud Run uses Docker; standalone trims the image to just the runtime
  // files + a minimal server.js (see node_modules/next/dist/docs/01-app/03-api-reference/05-config/01-next-config-js/output.md).
  output: "standalone",
};

export default nextConfig;
