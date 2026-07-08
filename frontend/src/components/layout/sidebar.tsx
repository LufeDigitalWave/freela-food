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
} from "lucide-react";

import { cn } from "@/lib/utils";

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

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 border-r bg-card">
      <div className="flex flex-col flex-1 min-h-0 pt-5 pb-4">
        <div className="flex items-center flex-shrink-0 px-4 mb-8">
          <h1 className="text-xl font-bold text-primary">🍽️ freela-food</h1>
        </div>
        <nav className="flex-1 px-2 space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
