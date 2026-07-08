"use client";

import { useEffect, useState } from "react";
import { Briefcase, ClipboardList, CreditCard, Star } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contratos ativos</CardTitle>
            <ClipboardList className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeContracts.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total contratos</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{contracts?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Não lidas</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{notifications?.unread_count || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pagamentos</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent contracts */}
      <Card>
        <CardHeader>
          <CardTitle>Contratos recentes</CardTitle>
        </CardHeader>
        <CardContent>
          {contracts?.items.length === 0 ? (
            <p className="text-muted-foreground text-sm">Nenhum contrato ainda.</p>
          ) : (
            <div className="space-y-3">
              {contracts?.items.slice(0, 5).map((c) => (
                <div key={c.id} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <p className="text-sm font-medium">
                      {new Date(c.start_at).toLocaleDateString("pt-BR")} —{" "}
                      {new Date(c.end_at).toLocaleDateString("pt-BR")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : "—"}
                    </p>
                  </div>
                  <Badge variant={c.status === "completed" ? "default" : c.status === "cancelled" ? "destructive" : "secondary"}>
                    {c.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent notifications */}
      <Card>
        <CardHeader>
          <CardTitle>Notificações recentes</CardTitle>
        </CardHeader>
        <CardContent>
          {notifications?.items.length === 0 ? (
            <p className="text-muted-foreground text-sm">Nenhuma notificação.</p>
          ) : (
            <div className="space-y-2">
              {notifications?.items.slice(0, 5).map((n) => (
                <div key={n.id} className="flex items-center justify-between">
                  <span className="text-sm">{n.type.replace(".", " → ")}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(n.created_at).toLocaleDateString("pt-BR")}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
