/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Cross-package source files (shared-types) are TS, so let Next transpile them.
  transpilePackages: ["@kashmiratlas/shared-types"],
  // Cesium ships its static Workers/Assets/Widgets; we copy them into public/cesium
  // via scripts/copy-cesium.mjs and reference them through CESIUM_BASE_URL=/cesium.
  env: {
    CESIUM_BASE_URL: "/cesium",
  },
  webpack: (config) => {
    // Cesium uses Node-style requires that webpack should not try to polyfill.
    config.resolve.fallback = { ...config.resolve.fallback, fs: false, path: false };
    return config;
  },
};

export default nextConfig;
