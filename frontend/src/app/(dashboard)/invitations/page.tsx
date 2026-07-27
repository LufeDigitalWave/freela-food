"use client";

import { useEffect, useState } from "react";
import { Send, Clock, CheckCircle, XCircle, Undo2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/use-auth";
import type { Invitation, InvitationList } from "@/lib/types";

const statusConfig: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: "Pendente", color: "bg-yellow-50 text-yellow-700", icon: Clock },
  accepted: { label: "Aceito", color: "bg-green-50 text-green-700", icon: CheckCircle },
  declined: { label: "Recusado", color: "bg-red-50 text-red-600", icon: XCircle },
  withdrawn: { label: "Retirado", color: "bg-gray-100 text-gray-600", icon: Undo2 },
  expired: { label: "Expirado", color: "bg-gray-100 text-gray-500", icon: Clock },
};

export default function InvitationsPage() {
  const { user } = useAuth();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const isEstablishment = user?.role === "establishment";

  useEffect(() => {
    api
      .get<InvitationList>("/invitations", { params: { page_size: 50 } })
      .then(({ data }) => setInvitations(data.items))
      .catch(() => showToast("Erro ao carregar convites", "error"))
      .finally(() => setLoading(false));
  }, []);

  const handleAction = async (invId: string, action: "accept" | "decline" | "withdraw") => {
    try {
      await api.post(`/invitations/${invId}/${action}`);
      setInvitations((prev) =>
        prev.map((inv) =>
          inv.id === invId
            ? { ...inv, status: action === "accept" ? "accepted" : action === "decline" ? "declined" : "withdrawn" }
            : inv
        )
      );
      const msgs = {
        accept: "Convite aceito! Contrato criado.",
        decline: "Convite recusado.",
        withdraw: "Convite retirado.",
      };
      showToast(msgs[action], "success");
    } catch {
      showToast("Erro ao processar convite", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
          {isEstablishment ? "Convites enviados" : "Convites recebidos"}
        </h2>
        <p className="text-gray-500 mt-1">
          {isEstablishment
            ? "Convites diretos enviados a freelancers"
            : "Convites recebidos de estabelecimentos"}
        </p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 skeleton rounded-2xl" />
          ))}
        </div>
      ) : invitations.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <Send className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">
            {isEstablishment ? "Nenhum convite enviado" : "Nenhum convite recebido"}
          </p>
          {isEstablishment && (
            <p className="text-sm text-gray-400 mt-1">Busque freelancers e envie convites diretos</p>
          )}
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          {invitations.map((inv) => {
            const cfg = statusConfig[inv.status] || statusConfig.pending;
            return (
              <div key={inv.id} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900">
                      {isEstablishment
                        ? `Freelancer #${inv.freelancer_id.slice(0, 8)}`
                        : `Estabelecimento #${inv.establishment_id.slice(0, 8)}`}
                    </p>
                    <div className="flex flex-wrap items-center gap-3 mt-1.5 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {new Date(inv.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                      </span>
                      {inv.proposed_hourly_rate && <span>R$ {inv.proposed_hourly_rate}/h</span>}
                      {inv.proposed_total_pay && <span>R$ {inv.proposed_total_pay} total</span>}
                    </div>
                    {inv.message && (
                      <p className="text-xs text-gray-500 mt-1 truncate">&#8220;{inv.message}&#8221;</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Badge className={`${cfg.color} rounded-full px-2.5 text-[11px] font-semibold`}>
                      {cfg.label}
                    </Badge>

                    {inv.status === "pending" && !isEstablishment && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-full text-red-600 border-red-200 hover:bg-red-50"
                          onClick={() => handleAction(inv.id, "decline")}
                        >
                          <XCircle className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          size="sm"
                          className="rounded-full bg-green-600 hover:bg-green-700"
                          onClick={() => handleAction(inv.id, "accept")}
                        >
                          <CheckCircle className="h-3.5 w-3.5" /> Aceitar
                        </Button>
                      </>
                    )}

                    {inv.status === "pending" && isEstablishment && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-full"
                        onClick={() => handleAction(inv.id, "withdraw")}
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
