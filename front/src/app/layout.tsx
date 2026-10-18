import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Helio | The company graph that answers itself",
  description:
    "Ask who owns what, what breaks if a service dies, and where a decision was actually made. Helio walks a live knowledge graph and shows every edge that produced the answer.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
    >
      <body className="body">{children}</body>
    </html>
  );
}
