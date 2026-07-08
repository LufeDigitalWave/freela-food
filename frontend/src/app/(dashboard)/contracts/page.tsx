"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { ContractList } from "@/lib/types";

const statusColors: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  scheduled: "secondary",
  in_progress: "default",
  completed: "outline",
  cancelled: "destructive",
};

export default function ContractsPage() {
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [tab, setTab] = useState("all");

  useEffect(() => {
    const params = tab === "all" ? {} : { status: tab };
    api.get<ContractList>("/me/contracts", { params: { ...params, page_size: 50 } })
      .then(({ data }) => setContracts(data));
  }, [tab]);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Meus contratos</h2>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="all">Todos</TabsTrigger>
          <TabsTrigger value="scheduled">Agendados</TabsTrigger>
          <TabsTrigger value="in_progress">Em andamento</TabsTrigger>
          <TabsTrigger value="completed">Concluídos</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelados</TabsTrigger>
        </TabsList>

        <TabsContent value={tab} className="mt-4">
          {!contracts ? (
            <p className="text-muted-foreground">Carregando...</p>
          ) : contracts.items.length === 0 ? (
            <p className="text-muted-foreground text-sm">Nenhum contrato nesta categoria.</p>
          ) : (
            <div className="space-y-3">
              {contracts.items.map((c) => (
                <Link key={c.id} href={`/contracts/${c.id}`}>
                  <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
                    <CardContent className="pt-4 flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">
                          {new Date(c.start_at).toLocaleDateString("pt-BR")} —{" "}
                          {new Date(c.end_at).toLocaleDateString("pt-BR")}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {c.agreed_hourly_rate
                            ? `R$ ${c.agreed_hourly_rate}/h`
                            : c.agreed_total_pay
                            ? `R$ ${c.agreed_total_pay}`
                            : "Valor a combinar"}
                        </p>
                      </div>
                      <Badge variant={statusColors[c.status]}>{c.status}</Badge>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
