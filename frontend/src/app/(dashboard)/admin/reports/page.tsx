"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";

interface AdminReport {
  id: string;
  reporter_id: string;
  target_type: string;
  target_id: string;
  reason: string;
  status: "open" | "resolved";
  created_at: string;
}

const statusColor = {
  open: "bg-red-50 text-red-600",
  resolved: "bg-green-50 text-green-700",
};

export default function AdminReportsPage() {
  const [reports, setReports] = useState<AdminReport[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get<{ items: AdminReport[] }>("/admin/reports", { params: { page_size: 50 } })
      .then(({ data }) => setReports(data.items))
      .catch(() => showToast("Erro ao carregar denúncias", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const resolve = async (id: string) => {
    try {
      await api.post(`/admin/reports/${id}/resolve`);
      showToast("Denúncia resolvida", "success");
      load();
    } catch {
      showToast("Erro ao resolver denúncia", "error");
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-900">Denúncias</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 skeleton rounded-2xl" />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Nenhuma denúncia.</p>
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <div key={r.id} className="bg-white rounded-2xl p-4 ring-1 ring-black/[0.04] shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className={statusColor[r.status]}>{r.status === "open" ? "Aberta" : "Resolvida"}</Badge>
                    <span className="text-xs text-gray-400">{new Date(r.created_at).toLocaleDateString("pt-BR")}</span>
                  </div>
                  <p className="text-sm text-gray-900">Motivo: {r.reason}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {r.target_type} · #{r.target_id.slice(0, 8)}
                  </p>
                </div>
                {r.status === "open" && (
                  <Button size="sm" onClick={() => resolve(r.id)} className="rounded-full shrink-0">
                    <Check className="h-3.5 w-3.5" /> Resolver
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}