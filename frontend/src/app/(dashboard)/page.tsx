"use client";

import { useEffect, useState } from "react";
import { Briefcase, ClipboardList, CreditCard, Bell, ArrowRight, PlusCircle, Users, Send } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ContractList, NotificationList } from "@/lib/types";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user } = useAuth();

  if (user?.role === "establishment") {
    return <EstablishmentDashboard />;
  }
  return <FreelancerDashboard />;
}

// ─── Freelancer Dashboard ────────────────────────────────────────────────────

function FreelancerDashboard() {
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [notifications, setNotifications] = useState<NotificationList | null>(null);

  useEffect(() => {
    api.get<ContractList>("/me/contracts?page_size=5").then(({ data }) => setContracts(data));
    api.get<NotificationList>("/me/notifications?page_size=5").then(({ data }) => setNotifications(data));
  }, []);

  const activeContracts = contracts?.items.filter(
    (c) => c.status === "scheduled" || c.status === "in_progress"
  ) || [];

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bom dia" : hour < 18 ? "Boa tarde" : "Boa noite";

  return (
    <div className="space-y-8">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">{greeting}! 👋</h2>
        <p className="text-gray-500 mt-1">Resumo da sua atividade na plataforma</p>
      </div>

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
        <DashboardCard
          title="Contratos recentes"
          linkHref="/contracts"
          emptyIcon={<ClipboardList className="h-6 w-6 text-gray-300" />}
          emptyText="Nenhum contrato ainda"
          emptyCta={{ href: "/jobs", label: "Buscar vagas" }}
          items={contracts?.items.slice(0, 4)}
          renderItem={(c) => (
            <Link key={c.id} href={`/contracts/${c.id}`} className="flex items-center justify-between py-3.5 hover:bg-gray-50 rounded-lg -mx-2 px-2 transition-colors">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {new Date(c.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} — {new Date(c.end_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : ""}
                </p>
              </div>
              <StatusBadge status={c.status} />
            </Link>
          )}
        />

        <DashboardCard
          title="Notificações"
          linkHref="/notifications"
          emptyIcon={<Bell className="h-6 w-6 text-gray-300" />}
          emptyText="Nenhuma notificação"
          items={notifications?.items.slice(0, 5)}
          renderItem={(n) => (
            <div key={n.id} className={`flex items-center justify-between py-3 ${n.read_at ? "opacity-50" : ""}`}>
              <div className="flex items-center gap-3">
                {!n.read_at && <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />}
                <div>
                  <p className="text-sm font-medium text-gray-700">{n.type.replace(/\./g, " → ")}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{new Date(n.created_at).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</p>
                </div>
              </div>
            </div>
          )}
        />
      </div>
    </div>
  );
}

// ─── Establishment Dashboard ─────────────────────────────────────────────────

function EstablishmentDashboard() {
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [notifications, setNotifications] = useState<NotificationList | null>(null);

  useEffect(() => {
    api.get<ContractList>("/me/contracts?page_size=5").then(({ data }) => setContracts(data));
    api.get<NotificationList>("/me/notifications?page_size=5").then(({ data }) => setNotifications(data));
  }, []);

  const activeContracts = contracts?.items.filter(
    (c) => c.status === "scheduled" || c.status === "in_progress"
  ) || [];

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Bom dia" : hour < 18 ? "Boa tarde" : "Boa noite";

  return (
    <div className="space-y-8">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">{greeting}! 🏪</h2>
        <p className="text-gray-500 mt-1">Painel do seu estabelecimento</p>
      </div>

      {/* Quick actions */}
      <div className="flex gap-3 anim-in-d1">
        <Link href="/jobs/new">
          <Button className="rounded-full gap-2 h-10">
            <PlusCircle className="h-4 w-4" /> Criar vaga
          </Button>
        </Link>
        <Link href="/jobs">
          <Button variant="outline" className="rounded-full gap-2 h-10">
            <Users className="h-4 w-4" /> Buscar freelancers
          </Button>
        </Link>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4 anim-in-d2">
        {[
          { label: "Contratos ativos", value: activeContracts.length, icon: ClipboardList, bg: "bg-orange-50", iconColor: "text-primary" },
          { label: "Total contratos", value: contracts?.total || 0, icon: Briefcase, bg: "bg-blue-50", iconColor: "text-blue-600" },
          { label: "Não lidas", value: notifications?.unread_count || 0, icon: Bell, bg: "bg-amber-50", iconColor: "text-amber-600" },
          { label: "Convites", value: "—", icon: Send, bg: "bg-purple-50", iconColor: "text-purple-600" },
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

      <div className="grid gap-6 lg:grid-cols-2 anim-in-d3">
        <DashboardCard
          title="Contratos recentes"
          linkHref="/contracts"
          emptyIcon={<ClipboardList className="h-6 w-6 text-gray-300" />}
          emptyText="Nenhum contrato ainda"
          emptyCta={{ href: "/jobs/new", label: "Criar vaga" }}
          items={contracts?.items.slice(0, 4)}
          renderItem={(c) => (
            <Link key={c.id} href={`/contracts/${c.id}`} className="flex items-center justify-between py-3.5 hover:bg-gray-50 rounded-lg -mx-2 px-2 transition-colors">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {new Date(c.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} — {new Date(c.end_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : ""}
                </p>
              </div>
              <StatusBadge status={c.status} />
            </Link>
          )}
        />

        <DashboardCard
          title="Notificações"
          linkHref="/notifications"
          emptyIcon={<Bell className="h-6 w-6 text-gray-300" />}
          emptyText="Nenhuma notificação"
          items={notifications?.items.slice(0, 5)}
          renderItem={(n) => (
            <div key={n.id} className={`flex items-center justify-between py-3 ${n.read_at ? "opacity-50" : ""}`}>
              <div className="flex items-center gap-3">
                {!n.read_at && <div className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />}
                <div>
                  <p className="text-sm font-medium text-gray-700">{n.type.replace(/\./g, " → ")}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{new Date(n.created_at).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</p>
                </div>
              </div>
            </div>
          )}
        />
      </div>
    </div>
  );
}

// ─── Shared components ───────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; className: string }> = {
    scheduled: { label: "agendado", className: "bg-gray-100 text-gray-600" },
    in_progress: { label: "em andamento", className: "bg-blue-50 text-blue-700" },
    completed: { label: "concluído", className: "bg-green-50 text-green-700" },
    cancelled: { label: "cancelado", className: "bg-red-50 text-red-600" },
  };
  const cfg = config[status] || config.scheduled;
  return <Badge className={`${cfg.className} rounded-full px-2.5 text-[10px] font-semibold`}>{cfg.label}</Badge>;
}

function DashboardCard<T>({
  title,
  linkHref,
  emptyIcon,
  emptyText,
  emptyCta,
  items,
  renderItem,
}: {
  title: string;
  linkHref: string;
  emptyIcon: React.ReactNode;
  emptyText: string;
  emptyCta?: { href: string; label: string };
  items: T[] | undefined;
  renderItem: (item: T) => React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
        <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>{title}</h3>
        <Link href={linkHref}>
          <Button variant="ghost" size="sm" className="text-xs text-gray-400 hover:text-primary gap-1">
            Ver todos <ArrowRight className="h-3 w-3" />
          </Button>
        </Link>
      </div>
      <div className="px-6 py-3">
        {!items || items.length === 0 ? (
          <div className="text-center py-10">
            <div className="w-14 h-14 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-3">
              {emptyIcon}
            </div>
            <p className="text-sm text-gray-400 mb-3">{emptyText}</p>
            {emptyCta && (
              <Link href={emptyCta.href}>
                <Button size="sm" className="rounded-full">{emptyCta.label}</Button>
              </Link>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-50">{items.map(renderItem)}</div>
        )}
      </div>
    </div>
  );
}
