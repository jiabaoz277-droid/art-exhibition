import type { NextConfig } from "next";

// 注意：rewrites 目标地址在 build 时固化，构建前需设置 BACKEND_URL
const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` },
      { source: "/files/:path*", destination: `${BACKEND_URL}/files/:path*` },
    ];
  },
};

export default nextConfig;
