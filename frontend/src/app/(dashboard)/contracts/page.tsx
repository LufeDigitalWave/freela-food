"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ClipboardList } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { ContractList } from "@/lib/types";

const statusConfig: Record<string, { label: string; color: string }> = {
  scheduled: { label: "Agendado", color: "bg-gray-100 text-gray-600" },
  in_progress: { label: "Em andamento", color: "bg-blue-50 text-blue-700" },
  completed: { label: "Concluído", color: "bg-green-50 text-green-700" },
  cancelled: { label: "Cancelado", color: "bg-red-50 text-red-600" },
};

const tabs = [
  { key: "all", label: "Todos" },
  { key: "scheduled", label: "Agendados" },
  { key: "in_progress", label: "Em andamento" },
  { key: "completed", label: "Concluídos" },
  { key: "cancelled", label: "Cancelados" },
];

export default function ContractsPage() {
  const [contracts, setContracts] = useState<ContractList | null>(null);
  const [tab, setTab] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = tab === "all" ? { page_size: 50 } : { status: tab, page_size: 50 };
    api.get<ContractList>("/me/contracts", { params })
      .then(({ data }) => setContracts(data))
      .finally(() => setLoading(false));
  }, [tab]);

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Meus contratos</h2>
        <p className="text-gray-500 mt-1">Histórico completo de serviços</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit anim-in-d1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-[72px] skeleton rounded-2xl" />
          ))}
        </div>
      ) : !contracts || contracts.items.length === 0 ? (
        <div className="text-center py-16 anim-in-d2">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <ClipboardList className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Nenhum contrato nesta categoria</p>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d2">
          {contracts.items.map((c) => {
            const cfg = statusConfig[c.status] || statusConfig.scheduled;
            return (
              <Link key={c.id} href={`/contracts/${c.id}`}>
                <div className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(c.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })} — {new Date(c.end_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {c.agreed_hourly_rate ? `R$ ${c.agreed_hourly_rate}/h` : c.agreed_total_pay ? `R$ ${c.agreed_total_pay}` : "Valor a combinar"}
                        {c.no_show && " • ⚠️ No-show"}
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
