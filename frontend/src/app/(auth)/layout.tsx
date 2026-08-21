import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Entrar | freela-food",
  description: "Faça login no freela-food para acessar vagas, contratos e gerenciar sua carreira no food service.",
  robots: { index: false, follow: false },
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
