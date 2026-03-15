import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BTC Market Intelligence",
  description: "Real-time Bitcoin sentiment, technicals, and market structure",
};

function Navbar() {
  return (
    <nav className="border-b border-white/8 bg-[#0a0a0f]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-1">
          <Link
            href="/"
            className="px-3 py-1.5 text-sm font-medium rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-all"
          >
            Sentiment
          </Link>
          <Link
            href="/market-setup"
            className="px-3 py-1.5 text-sm font-medium rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-all"
          >
            Market Setup
          </Link>
        </div>
        <div className="text-xs text-slate-600">BTC Market Intelligence</div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} dark bg-[#0a0a0f]`}>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
