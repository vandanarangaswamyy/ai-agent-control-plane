const backendInternalUrl = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendInternalUrl}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backendInternalUrl}/health`,
      },
      {
        source: "/ready",
        destination: `${backendInternalUrl}/ready`,
      },
      {
        source: "/metrics",
        destination: `${backendInternalUrl}/metrics`,
      },
    ];
  },
};

export default nextConfig;
