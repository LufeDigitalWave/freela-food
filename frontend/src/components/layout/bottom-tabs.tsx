"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, ShoppingBag, FileText, Bell, User, Users, Send } from "lucide-react";

import { cn } from "@/lib/utils";
import type { User as UserType } from "@/lib/types";

interface TabItem {
  icon: typeof Home;
  label: string;
  href: string;
  matchPrefix?: string;
}

const freelancerTabs: TabItem[] = [
  { icon: Home, label: "Início", href: "/" },
  { icon: ShoppingBag, label: "Vagas", href: "/jobs", matchPrefix: "/jobs" },
  { icon: FileText, label: "Candidaturas", href: "/applications" },
  { icon: Bell, label: "Notif", href: "/notifications" },
  { icon: User, label: "Perfil", href: "/profile" },
];

const establishmentTabs: TabItem[] = [
  { icon: Home, label: "Início", href: "/" },
  { icon: ShoppingBag, label: "Vagas", href: "/jobs/mine", matchPrefix: "/jobs" },
  { icon: Users, label: "Candidatos", href: "/candidates" },
  { icon: Send, label: "Convites", href: "/invitations" },
  { icon: User, label: "Perfil", href: "/profile" },
];

export function BottomTabs({ user }: { user: UserType | null }) {
  const pathname = usePathname();

  const tabs = user?.role === "establishment" ? establishmentTabs : freelancerTabs;

  return (
    <nav
      aria-label="Navegação principal"
      className="fixed bottom-0 inset-x-0 z-30 md:hidden bg-white border-t border-gray-100 pb-[env(safe-area-inset-bottom)]"
    >
      <ul className="flex justify-around">
        {tabs.map(({ icon: Icon, label, href, matchPrefix }) => {
          const isActive =
            pathname === href || (matchPrefix ? pathname.startsWith(matchPrefix) : false);
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 py-2.5 text-[11px] font-medium transition-colors",
                  isActive ? "text-primary" : "text-gray-500 hover:text-gray-700"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="h-5 w-5" aria-hidden />
                <span>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}