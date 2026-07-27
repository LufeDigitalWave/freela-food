"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";

interface AdminPayment {
  id: string;
  contract_id: string;
  amount: string;
  status: "pending" | "confirmed" | "disputed";
  created_at: string;
}

const statusColor = {
  pending: "bg-yellow-50 text-yellow-700",
  confirmed: "bg-green-50 text-green-700",
  disputed: "bg-red-50 text-red-600",
};

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<AdminPayment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ items: AdminPayment[] }>("/admin/payments", { params: { page_size: 50 } })
      .then(({ data }) => setPayments(data.items || []))
      .catch(() => showToast("Erro ao carregar pagamentos", "error"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-900">Pagamentos</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 skeleton rounded-2xl" />
          ))}
        </div>
      ) : payments.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Nenhum pagamento.</p>
      ) : (
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-xs uppercase text-gray-400">
              <tr>
                <th className="px-4 py-3 text-left">Contrato</th>
                <th className="px-4 py-3 text-left">Valor</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {payments.map((p) => (
                <tr key={p.id}>
                  <td className="px-4 py-3 text-sm">#{p.contract_id.slice(0, 8)}</td>
                  <td className="px-4 py-3 text-sm font-medium">R$ {p.amount}</td>
                  <td className="px-4 py-3">
                    <Badge className={statusColor[p.status]}>
                      {p.status === "pending" ? "Pendente" : p.status === "confirmed" ? "Confirmado" : "Disputado"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {new Date(p.created_at).toLocaleDateString("pt-BR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}