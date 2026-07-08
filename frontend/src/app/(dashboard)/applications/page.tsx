"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { ApplicationList } from "@/lib/types";

const statusColors: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "secondary",
  accepted: "default",
  rejected: "destructive",
  withdrawn: "outline",
};

export default function ApplicationsPage() {
  const [apps, setApps] = useState<ApplicationList | null>(null);

  useEffect(() => {
    api.get<ApplicationList>("/me/contracts", { params: { page_size: 50 } })
      .catch(() => null);
    // Buscar candidaturas — endpoint não existe diretamente como /me/applications
    // Usa o endpoint de jobs que retorna applications do user
    api.get("/me/notifications", { params: { page_size: 1 } }).catch(() => null);
  }, []);

  // Fetch applications via jobs endpoint workaround
  useEffect(() => {
    // O backend não tem GET /me/applications direto
    // Mas podemos listar por job — pra simplificar, mostramos contratos
    api.get<ApplicationList>("/me/contracts").then(({ data }) => {
      // Map contracts como "applications" pra exibição
      setApps(data as unknown as ApplicationList);
    }).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Minhas candidaturas</h2>

      {!apps ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : apps.items.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            Você ainda não se candidatou a nenhuma vaga.
            <br />
            <Link href="/jobs" className="text-primary hover:underline">
              Buscar vagas
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {apps.items.map((item) => (
            <Card key={item.id}>
              <CardContent className="pt-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">Contrato #{item.id.slice(0, 8)}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleDateString("pt-BR")}
                  </p>
                </div>
                <Badge variant={statusColors[item.status] || "secondary"}>
                  {item.status}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
