"use client";

import { useEffect, useState } from "react";
import { CreditCard } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { PaymentList } from "@/lib/types";

const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: "Pendente", color: "bg-yellow-50 text-yellow-700" },
  confirmed: { label: "Confirmado", color: "bg-green-50 text-green-700" },
  disputed: { label: "Disputado", color: "bg-red-50 text-red-600" },
};

export default function PaymentsPage() {
  const [payments, setPayments] = useState<PaymentList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<PaymentList>("/me/payments")
      .then(({ data }) => setPayments(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Pagamentos</h2>
        <p className="text-gray-500 mt-1">Histórico de pagamentos dos contratos</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 skeleton rounded-2xl" />
          ))}
        </div>
      ) : !payments || payments.items.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <CreditCard className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Nenhum pagamento registrado</p>
          <p className="text-sm text-gray-400 mt-1">Pagamentos aparecem após conclusão de contratos</p>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          {payments.items.map((p) => {
            const cfg = statusConfig[p.status] || statusConfig.pending;
            return (
              <div key={p.id} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-lg font-bold text-gray-900">R$ {p.amount}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                      <span>{new Date(p.created_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })}</span>
                      {p.pix_key && <span>Pix: {p.pix_key}</span>}
                    </div>
                    {p.notes && <p className="text-xs text-gray-500 mt-1.5">{p.notes}</p>}
                    {p.confirmed_at && (
                      <p className="text-xs text-green-600 mt-1">
                        Confirmado em {new Date(p.confirmed_at).toLocaleString("pt-BR")}
                      </p>
                    )}
                  </div>
                  <Badge className={`${cfg.color} rounded-full px-2.5 text-[11px] font-semibold`}>
                    {cfg.label}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
