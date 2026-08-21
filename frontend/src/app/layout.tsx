import type { Metadata, Viewport } from "next";
import { Inter, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast";
import { ServiceWorkerRegistration } from "@/components/service-worker-registration";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: ["400"],
  style: ["normal", "italic"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#e85d2c",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export const metadata: Metadata = {
  title: "freela-food | Marketplace de Food Service",
  description: "Conectando talentos da gastronomia a oportunidades. Encontre vagas, gerencie contratos e cresça na carreira.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "freela-food",
  },
  formatDetection: {
    telephone: false,
  },
  icons: [
    { rel: "icon", url: "/favicon.ico" },
    { rel: "apple-touch-icon", url: "/icon-192.png" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${instrumentSerif.variable} h-full`}>
      <body className="min-h-full flex flex-col font-sans antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-primary focus:text-white focus:font-semibold focus:text-sm focus:shadow-lg"
        >
          Pular para o conteúdo
        </a>
        {children}
        <ToastProvider />
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
