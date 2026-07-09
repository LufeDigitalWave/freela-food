"use client";

import { useEffect, useState } from "react";
import { Send, Clock, CheckCircle, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface Invitation {
  id: string;
  freelancer_id: string;
  status: string;
  start_at: string;
  end_at: string;
  proposed_hourly_rate: string | null;
  created_at: string;
}

interface InvitationList {
  items: Invitation[];
  total: number;
}

const statusConfig: Record<string, { label: string; color: string; icon: typeof Clock }> = {
  pending: { label: "Pendente", color: "bg-yellow-50 text-yellow-700", icon: Clock },
  accepted: { label: "Aceito", color: "bg-green-50 text-green-700", icon: CheckCircle },
  declined: { label: "Recusado", color: "bg-red-50 text-red-600", icon: XCircle },
  withdrawn: { label: "Retirado", color: "bg-gray-100 text-gray-600", icon: XCircle },
  expired: { label: "Expirado", color: "bg-gray-100 text-gray-500", icon: Clock },
};

export default function InvitationsPage() {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<InvitationList>("/invitations", { params: { page_size: 50 } })
      .then(({ data }) => setInvitations(data.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Convites enviados</h2>
        <p className="text-gray-500 mt-1">Convites diretos enviados a freelancers</p>
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
          <p className="text-gray-500">Nenhum convite enviado ainda</p>
          <p className="text-sm text-gray-400 mt-1">Busque freelancers e envie convites diretos</p>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          {invitations.map((inv) => {
            const cfg = statusConfig[inv.status] || statusConfig.pending;
            return (
              <div key={inv.id} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Freelancer #{inv.freelancer_id.slice(0, 8)}</p>
                    <div className="flex items-center gap-3 mt-1.5 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {new Date(inv.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                      </span>
                      {inv.proposed_hourly_rate && <span>R$ {inv.proposed_hourly_rate}/h</span>}
                    </div>
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
