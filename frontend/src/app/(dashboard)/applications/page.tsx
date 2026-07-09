"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ContractList } from "@/lib/types";

const statusConfig: Record<string, { label: string; color: string }> = {
  scheduled: { label: "Aceita", color: "bg-green-50 text-green-700" },
  in_progress: { label: "Em andamento", color: "bg-blue-50 text-blue-700" },
  completed: { label: "Concluída", color: "bg-gray-100 text-gray-600" },
  cancelled: { label: "Cancelada", color: "bg-red-50 text-red-600" },
};

export default function ApplicationsPage() {
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ContractList>("/me/contracts", { params: { page_size: 50 } })
      .then(({ data }) => setContracts(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Minhas candidaturas</h2>
        <p className="text-gray-500 mt-1">Vagas em que você se candidatou</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-[72px] skeleton rounded-2xl" />
          ))}
        </div>
      ) : !contracts || contracts.items.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <FileText className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Você ainda não se candidatou a nenhuma vaga</p>
          <Link href="/jobs" className="mt-4 inline-block">
            <Button className="rounded-full">Buscar vagas</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          {contracts.items.map((c) => {
            const cfg = statusConfig[c.status] || statusConfig.scheduled;
            return (
              <Link key={c.id} href={`/contracts/${c.id}`}>
                <div className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Contrato #{c.id.slice(0, 8)}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(c.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })} — {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : ""}
                      </p>
                    </div>
                    <Badge className={`${cfg.color} rounded-full px-2.5 text-[11px] font-semibold`}>
                      {cfg.label}
                    </Badge>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
