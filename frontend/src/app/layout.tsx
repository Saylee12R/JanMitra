import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "JanMitra – Personal Government Services Assistant",
  description: "Discover government schemes and services you may be eligible for — based on your age, location, occupation and circumstances.",
  keywords: "government schemes, India, eligibility, scholarships, PM-KISAN, Ayushman Bharat",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="min-h-screen">{children}</main>
        <footer className="border-t border-gray-200 bg-white py-8 mt-12">
          <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-500">
            <p className="font-semibold text-gray-700 mb-1">JanMitra — Personal Government Services Assistant</p>
            <p>JanMitra is an informational tool. Final eligibility and application requirements should be confirmed on official government websites.</p>
            <p className="mt-2">Built for Hackathon • Not an official government service</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
