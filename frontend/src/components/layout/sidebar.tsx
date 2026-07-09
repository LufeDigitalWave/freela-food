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
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/use-auth";

const navItems = [
  { href: "/", icon: Home, label: "Dashboard" },
  { href: "/profile", icon: User, label: "Perfil" },
  { href: "/jobs", icon: Briefcase, label: "Vagas" },
  { href: "/applications", icon: FileText, label: "Candidaturas" },
  { href: "/contracts", icon: ClipboardList, label: "Contratos" },
  { href: "/reviews", icon: Star, label: "Avaliações" },
  { href: "/payments", icon: CreditCard, label: "Pagamentos" },
  { href: "/notifications", icon: Bell, label: "Notificações" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r border-border/50"
      style={{ background: "var(--sidebar)" }}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-border/30">
        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
          <span className="text-base">🍽️</span>
        </div>
        <span className="font-bold text-lg gradient-text">freela-food</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary/15 text-primary shadow-sm"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              <item.icon className={cn(
                "h-4 w-4 transition-transform duration-200",
                isActive ? "text-primary" : "group-hover:scale-110"
              )} />
              {item.label}
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="px-3 pb-4 border-t border-border/30 pt-3">
        <div className="flex items-center gap-3 px-3 py-2.5">
          <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
            {user?.email?.[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
