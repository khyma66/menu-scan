import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  webpack: (config, { isServer }) => {
    // Disable Turbopack features
    config.experiments = {
      ...config.experiments,
      cacheUnaffected: true,
    };
    return config;
  }
};

export default nextConfig;
