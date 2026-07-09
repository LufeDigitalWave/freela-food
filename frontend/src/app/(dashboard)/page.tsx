"use client";

import { useEffect, useState } from "react";
import { Briefcase, ClipboardList, CreditCard, Bell, ArrowRight } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ContractList, NotificationList } from "@/lib/types";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user } = useAuth();
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [notifications, setNotifications] = useState<NotificationList | null>(null);

  useEffect(() => {
    api.get<ContractList>("/me/contracts?page_size=5").then(({ data }) => setContracts(data));
    api.get<NotificationList>("/me/notifications?page_size=5").then(({ data }) => setNotifications(data));
  }, []);

  const activeContracts = contracts?.items.filter(
    (c) => c.status === "scheduled" || c.status === "in_progress"
  ) || [];

  // Greeting based on time
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bom dia" : hour < 18 ? "Boa tarde" : "Boa noite";

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900"  >
          {greeting}! 👋
        </h2>
        <p className="text-gray-500 mt-1">Resumo da sua atividade na plataforma</p>
      </div>

      {/* Stats */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4 anim-in-d1">
        {[
          { label: "Ativos", value: activeContracts.length, icon: ClipboardList, bg: "bg-orange-50", iconColor: "text-primary" },
          { label: "Contratos", value: contracts?.total || 0, icon: Briefcase, bg: "bg-blue-50", iconColor: "text-blue-600" },
          { label: "Não lidas", value: notifications?.unread_count || 0, icon: Bell, bg: "bg-amber-50", iconColor: "text-amber-600" },
          { label: "Pagamentos", value: "—", icon: CreditCard, bg: "bg-green-50", iconColor: "text-green-600" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1.5">{stat.value}</p>
              </div>
              <div className={`stat-bubble ${stat.bg}`}>
                <stat.icon className={`h-5 w-5 ${stat.iconColor}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="divider-gradient" />

      <div className="grid gap-6 lg:grid-cols-2 anim-in-d2">
        {/* Contracts */}
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
            <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Contratos recentes</h3>
            <Link href="/contracts">
              <Button variant="ghost" size="sm" className="text-xs text-gray-400 hover:text-primary gap-1">
                Ver todos <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
          <div className="px-6 py-3">
            {contracts?.items.length === 0 ? (
              <div className="text-center py-10">
                <div className="w-14 h-14 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-3">
                  <ClipboardList className="h-6 w-6 text-gray-300" />
                </div>
                <p className="text-sm text-gray-400 mb-3">Nenhum contrato ainda</p>
                <Link href="/jobs">
                  <Button size="sm" className="rounded-full">Buscar vagas</Button>
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {contracts?.items.slice(0, 4).map((c) => (
                  <Link
                    key={c.id}
                    href={`/contracts/${c.id}`}
                    className="flex items-center justify-between py-3.5 hover:bg-gray-25 rounded-lg transition-colors -mx-2 px-2"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(c.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} — {new Date(c.end_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : ""}
                      </p>
                    </div>
                    <Badge className={`text-[10px] font-semibold rounded-full px-2.5 ${
                      c.status === "completed" ? "bg-green-50 text-green-700" :
                      c.status === "cancelled" ? "bg-red-50 text-red-600" :
                      c.status === "in_progress" ? "bg-blue-50 text-blue-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>
                      {c.status === "scheduled" ? "agendado" : c.status === "in_progress" ? "em andamento" : c.status === "completed" ? "concluído" : "cancelado"}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
            <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Notificações</h3>
            <Link href="/notifications">
              <Button variant="ghost" size="sm" className="text-xs text-gray-400 hover:text-primary gap-1">
                Ver todas <ArrowRight className="h-3 w-3" />
              </Button>
            </Link>
          </div>
          <div className="px-6 py-3">
            {notifications?.items.length === 0 ? (
              <div className="text-center py-10">
                <div className="w-14 h-14 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-3">
                  <Bell className="h-6 w-6 text-gray-300" />
                </div>
                <p className="text-sm text-gray-400">Nenhuma notificação</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {notifications?.items.slice(0, 5).map((n) => (
                  <div
                    key={n.id}
                    className={`flex items-center justify-between py-3 ${
                      n.read_at ? "opacity-50" : ""
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {!n.read_at && <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />}
                      <div>
                        <p className="text-sm font-medium text-gray-700">
                          {n.type.replace(/\./g, " → ")}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {new Date(n.created_at).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
