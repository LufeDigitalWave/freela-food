"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Briefcase,
  ClipboardList,
  CreditCard,
  FileText,
  Home,
  Bell,
  Star,
  User,
  LogOut,
  PlusCircle,
  Users,
  Send,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

const freelancerNav = [
  { href: "/", icon: Home, label: "Dashboard" },
  { href: "/profile", icon: User, label: "Perfil" },
  { href: "/jobs", icon: Briefcase, label: "Buscar vagas" },
  { href: "/applications", icon: FileText, label: "Candidaturas" },
  { href: "/contracts", icon: ClipboardList, label: "Contratos" },
  { href: "/reviews", icon: Star, label: "Avaliações" },
  { href: "/payments", icon: CreditCard, label: "Pagamentos" },
  { href: "/notifications", icon: Bell, label: "Notificações" },
];

const establishmentNav = [
  { href: "/", icon: Home, label: "Dashboard" },
  { href: "/profile", icon: User, label: "Perfil" },
  { href: "/jobs/mine", icon: Briefcase, label: "Minhas vagas" },
  { href: "/jobs/new", icon: PlusCircle, label: "Criar vaga" },
  { href: "/candidates", icon: Users, label: "Candidatos" },
  { href: "/invitations", icon: Send, label: "Convites" },
  { href: "/contracts", icon: ClipboardList, label: "Contratos" },
  { href: "/reviews", icon: Star, label: "Avaliações" },
  { href: "/payments", icon: CreditCard, label: "Pagamentos" },
  { href: "/notifications", icon: Bell, label: "Notificações" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = user?.role === "establishment" ? establishmentNav : freelancerNav;

  return (
    <aside className="hidden md:flex md:w-[260px] md:flex-col md:fixed md:inset-y-0 bg-[#f9fafb] border-r border-gray-100">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-6 h-[72px]">
        <span className="text-2xl">🍽️</span>
        <span className="text-lg font-bold gradient-text">freela-food</span>
      </div>

      {/* Role badge */}
      <div className="px-6 mb-3">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
          user?.role === "establishment"
            ? "bg-blue-50 text-blue-700"
            : "bg-orange-50 text-primary"
        }`}>
          {user?.role === "establishment" ? "🏪 Estabelecimento" : "👨‍🍳 Freelancer"}
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] font-medium transition-all duration-150",
                isActive
                  ? "bg-white text-primary shadow-sm ring-1 ring-black/[0.04]"
                  : "text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm hover:ring-1 hover:ring-black/[0.03]"
              )}
            >
              <item.icon className={cn(
                "h-[18px] w-[18px] transition-colors",
                isActive ? "text-primary" : "text-gray-400 group-hover:text-gray-600"
              )} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="px-3 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-3">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
            style={{ background: "linear-gradient(135deg, #e85d2c, #f59e0b)" }}>
            {user?.email?.[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            title="Sair"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
