"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, Users, AlertTriangle, Star, CreditCard, FileText, BarChart3 } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const adminNav = [
  { href: "/admin", icon: BarChart3, label: "Dashboard" },
  { href: "/admin/users", icon: Users, label: "Usuários" },
  { href: "/admin/reports", icon: AlertTriangle, label: "Denúncias" },
  { href: "/admin/reviews", icon: Star, label: "Avaliações" },
  { href: "/admin/payments", icon: CreditCard, label: "Pagamentos" },
  { href: "/admin/audit-log", icon: FileText, label: "Audit log" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();

  if (loading) return null;
  if (!user) return null;
  if (user.role !== "admin") {
    return (
      <div className="text-center py-16">
        <Shield className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900">Acesso restrito</h2>
        <p className="text-gray-500 mt-2">Apenas administradores podem acessar esta área.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Shield className="h-6 w-6 text-primary" />
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Painel Admin</h2>
      </div>

      <div className="bg-white rounded-2xl p-4 ring-1 ring-black/[0.04] shadow-sm">
        <nav className="flex gap-2 overflow-x-auto pb-1" aria-label="Admin nav">
          {adminNav.map(({ href, icon: Icon, label }) => {
            const isActive =
              pathname === href || (href !== "/admin" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium transition-colors whitespace-nowrap",
                  isActive
                    ? "bg-primary text-white"
                    : "text-gray-700 hover:bg-gray-50"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
      </div>

      {children}
    </div>
  );
}