"use client";

import { useEffect, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { PaymentList } from "@/lib/types";

const statusColors: Record<string, "default" | "secondary" | "destructive"> = {
  pending: "secondary",
  confirmed: "default",
  disputed: "destructive",
};

export default function PaymentsPage() {
  const [payments, setPayments] = useState<PaymentList | null>(null);

  useEffect(() => {
    api.get<PaymentList>("/me/payments").then(({ data }) => setPayments(data));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Pagamentos</h2>

      {!payments ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : payments.items.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            Nenhum pagamento registrado.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {payments.items.map((p) => (
            <Card key={p.id}>
              <CardContent className="pt-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">R$ {p.amount}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(p.created_at).toLocaleDateString("pt-BR")}
                    {p.pix_key && ` — Pix: ${p.pix_key}`}
                  </p>
                  {p.notes && <p className="text-xs text-muted-foreground mt-1">{p.notes}</p>}
                </div>
                <Badge variant={statusColors[p.status]}>{p.status}</Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
