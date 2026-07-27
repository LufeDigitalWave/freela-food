"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Undo2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";
import type { Application, ApplicationList } from "@/lib/types";

const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: "Pendente", color: "bg-yellow-50 text-yellow-700" },
  accepted: { label: "Aceita", color: "bg-green-50 text-green-700" },
  rejected: { label: "Rejeitada", color: "bg-red-50 text-red-600" },
  withdrawn: { label: "Retirada", color: "bg-gray-100 text-gray-600" },
};

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    api
      .get<ApplicationList>("/me/applications", { params: { page_size: 50 } })
      .then(({ data }) => {
        setApps(data.items);
        setTotal(data.total);
      })
      .catch(() => {
        showToast("Erro ao carregar candidaturas", "error");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleWithdraw = async (appId: string) => {
    try {
      await api.post(`/applications/${appId}/withdraw`);
      setApps((prev) => prev.map((a) => (a.id === appId ? { ...a, status: "withdrawn" as const } : a)));
      showToast("Candidatura retirada", "success");
    } catch {
      showToast("Erro ao retirar candidatura", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Minhas candidaturas</h2>
        <p className="text-gray-500 mt-1">Vagas em que você se candidatou</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-[72px] skeleton rounded-2xl" />
          ))}
        </div>
      ) : apps.length === 0 ? (
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
          <p className="text-sm text-gray-400">{total} candidatura{total !== 1 && "s"}</p>
          {apps.map((app) => {
            const cfg = statusConfig[app.status] || statusConfig.pending;
            return (
              <div key={app.id} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <Link href={`/jobs/${app.job_posting_id}`} className="hover:underline">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        Vaga #{app.job_posting_id.slice(0, 8)}
                      </p>
                    </Link>
                    {app.message && (
                      <p className="text-xs text-gray-500 mt-0.5 truncate">"{app.message}"</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(app.created_at).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge className={`${cfg.color} rounded-full px-2.5 text-[11px] font-semibold`}>
                      {cfg.label}
                    </Badge>
                    {app.status === "pending" && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-full"
                        onClick={() => handleWithdraw(app.id)}
                      >
                        <Undo2 className="h-3.5 w-3.5" /> Retirar
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
