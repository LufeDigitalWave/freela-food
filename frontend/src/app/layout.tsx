import type { Metadata } from "next";
import { Inter, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "freela-food | Marketplace de Food Service",
  description: "Conectando talentos da gastronomia a oportunidades. Encontre vagas, gerencie contratos e cresça na carreira.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${instrumentSerif.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans antialiased">
        {children}
        <ToastProvider />
      </body>
    </html>
  );
}
