"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { LogOut, Menu, X } from "lucide-react";

import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

const drawerItems = [
  { href: "/", label: "Dashboard" },
  { href: "/profile", label: "Perfil" },
  { href: "/reviews", label: "Avaliações" },
  { href: "/payments", label: "Pagamentos" },
];

export function MobileDrawer() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  const close = () => setOpen(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="md:hidden p-2.5 rounded-xl hover:bg-gray-50 transition-colors"
        aria-label="Abrir menu"
        aria-expanded={open}
      >
        <Menu className="h-5 w-5 text-gray-700" />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Menu lateral"
        >
          <div
            className="absolute inset-0 bg-black/40 animate-[fadeIn_0.2s_ease-out]"
            onClick={close}
          />
          <aside className="absolute inset-y-0 left-0 w-72 bg-white shadow-2xl flex flex-col animate-[slideInLeft_0.25s_ease-out]">
            <div className="flex items-center justify-between px-6 h-[72px] border-b border-gray-100">
              <div className="flex items-center gap-2.5">
                <span className="text-2xl">🍽️</span>
                <span className="text-lg font-bold gradient-text">freela-food</span>
              </div>
              <button
                type="button"
                onClick={close}
                aria-label="Fechar menu"
                className="p-2 rounded-lg hover:bg-gray-50"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <nav className="flex-1 px-3 py-4 overflow-y-auto" aria-label="Menu secundário">
              <ul className="space-y-0.5">
                {drawerItems.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/" && pathname.startsWith(item.href));
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={close}
                        className={cn(
                          "flex items-center px-3 py-2.5 rounded-xl text-[14px] font-medium transition-all",
                          isActive
                            ? "bg-primary/10 text-primary"
                            : "text-gray-700 hover:bg-gray-50"
                        )}
                      >
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </nav>

            <div className="px-3 py-4 border-t border-gray-100">
              <div className="px-3 py-2 mb-2">
                <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {user?.role === "establishment" ? "🏪 Estabelecimento" : "👨‍🍳 Freelancer"}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  close();
                  logout();
                }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] font-medium text-gray-700 hover:bg-gray-50"
              >
                <LogOut className="h-4 w-4" /> Sair
              </button>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
