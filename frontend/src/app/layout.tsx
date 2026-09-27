import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "ComplianceOS | GeM AI Bid Verifier",
  description: "AI-powered bid compliance verification and decision-support platform for GeM procurement.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={geist.variable}>
      <body>
        <div className="app-shell">
          <Sidebar />
          <div className="main-content">
            <TopBar />
            <main className="page-content">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
