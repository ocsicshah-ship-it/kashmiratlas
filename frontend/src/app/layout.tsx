import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kashmir Valley Capability Atlas",
  description: "Hybrid Google-Earth / map-style atlas of Kashmir Valley capabilities on an H3 grid.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
