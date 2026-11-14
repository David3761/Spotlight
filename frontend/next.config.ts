import path from "node:path";
import type { NextConfig } from "next";

/** The Next.js configuration: Cache Components, the Tailwind loader and the `/` → `/start` redirect. */
const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    root: path.join(__dirname),
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async redirects() {
    return [{ source: "/", destination: "/start", permanent: false }];
  },
};

export default nextConfig;
