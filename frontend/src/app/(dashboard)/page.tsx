"use client";

import { useEffect, useState } from "react";
import { Briefcase, ClipboardList, CreditCard, Star, TrendingUp, Bell } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ContractList, NotificationList } from "@/lib/types";

export default function DashboardPage() {
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [notifications, setNotifications] = useState<NotificationList | null>(null);

  useEffect(() => {
    api.get<ContractList>("/me/contracts?page_size=5").then(({ data }) => setContracts(data));
    api.get<NotificationList>("/me/notifications?page_size=5").then(({ data }) => setNotifications(data));
  }, []);

  const activeContracts = contracts?.items.filter(
    (c) => c.status === "scheduled" || c.status === "in_progress"
  ) || [];

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div className="animate-fade-in-up">
        <h2 className="text-3xl font-bold">Dashboard</h2>
        <p className="text-muted-foreground mt-1">Resumo da sua atividade na plataforma</p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-4 animate-fade-in-up-delay-1">
        {[
          { label: "Contratos ativos", value: activeContracts.length, icon: ClipboardList, color: "text-primary" },
          { label: "Total contratos", value: contracts?.total || 0, icon: Briefcase, color: "text-chart-2" },
          { label: "Não lidas", value: notifications?.unread_count || 0, icon: Bell, color: "text-chart-3" },
          { label: "Score", value: "—", icon: TrendingUp, color: "text-chart-1" },
        ].map((stat) => (
          <Card key={stat.label} className="glass-card border-border/30 hover:border-primary/30 transition-colors duration-300">
            <CardContent className="pt-5 pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">{stat.label}</p>
                  <p className="text-2xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`p-2.5 rounded-xl bg-secondary/60 ${stat.color}`}>
                  <stat.icon className="h-5 w-5" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2 animate-fade-in-up-delay-2">
        {/* Recent contracts */}
        <Card className="glass-card border-border/30">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Contratos recentes</CardTitle>
            <Link href="/contracts">
              <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">Ver todos</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {contracts?.items.length === 0 ? (
              <div className="text-center py-8">
                <ClipboardList className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
                <p className="text-muted-foreground text-sm">Nenhum contrato ainda</p>
                <Link href="/jobs" className="mt-3 inline-block">
                  <Button size="sm" className="mt-2">Buscar vagas</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {contracts?.items.slice(0, 4).map((c) => (
                  <Link
                    key={c.id}
                    href={`/contracts/${c.id}`}
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-secondary/40 transition-colors"
                  >
                    <div>
                      <p className="text-sm font-medium"  >
                        {new Date(c.start_at).toLocaleDateString("pt-BR")} — {new Date(c.end_at).toLocaleDateString("pt-BR")}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : ""}
                      </p>
                    </div>
                    <Badge
                      variant={c.status === "completed" ? "default" : c.status === "cancelled" ? "destructive" : "secondary"}
                      className="text-[10px]"
                    >
                      {c.status}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent notifications */}
        <Card className="glass-card border-border/30">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Notificações</CardTitle>
            <Link href="/notifications">
              <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">Ver todas</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {notifications?.items.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
                <p className="text-muted-foreground text-sm">Nenhuma notificação</p>
              </div>
            ) : (
              <div className="space-y-2">
                {notifications?.items.slice(0, 5).map((n) => (
                  <div
                    key={n.id}
                    className={`flex items-center justify-between p-3 rounded-xl ${
                      n.read_at ? "opacity-50" : "bg-primary/5 border border-primary/10"
                    }`}
                  >
                    <div>
                      <span className="text-sm font-medium">{n.type.replace(/\./g, " → ")}</span>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {new Date(n.created_at).toLocaleString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </p>
                    </div>
                    {!n.read_at && <div className="w-2 h-2 rounded-full bg-primary" />}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
