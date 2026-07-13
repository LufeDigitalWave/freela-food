"use client";

import { useEffect, useState } from "react";
import { Bell, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Pagination } from "@/components/ui/pagination";
import { api } from "@/lib/api";
import type { NotificationList } from "@/lib/types";

// Human-readable notification messages
const notifMessages: Record<string, string> = {
  "application.received": "Nova candidatura recebida na sua vaga",
  "application.accepted": "Sua candidatura foi aceita!",
  "application.rejected": "Sua candidatura foi recusada",
  "invitation.received": "Você recebeu um convite de trabalho",
  "invitation.accepted": "Seu convite foi aceito",
  "invitation.declined": "Seu convite foi recusado",
  "invitation.withdrawn": "Convite retirado",
  "contract.started": "Seu contrato começou",
  "contract.completed": "Contrato concluído com sucesso",
  "contract.cancelled_by_other_party": "Contrato cancelado pela outra parte",
  "review.peer_submitted": "A outra parte enviou uma avaliação",
  "review.both_visible": "Ambas avaliações estão visíveis",
  "review.revealed": "Sua avaliação ficou pública",
  "review.hidden": "Uma avaliação foi ocultada pela moderação",
  "payment.pending": "Pagamento pendente no seu contrato",
  "payment.confirmed": "Pagamento confirmado!",
  "payment.disputed": "Pagamento em disputa",
  "report.submitted": "Sua denúncia foi registrada",
  "report.resolved": "Sua denúncia foi resolvida",
};

function getNotifMessage(type: string): string {
  return notifMessages[type] || type.replace(/\./g, " → ");
}

function getNotifIcon(type: string): string {
  if (type.startsWith("application")) return "📋";
  if (type.startsWith("invitation")) return "📨";
  if (type.startsWith("contract")) return "📄";
  if (type.startsWith("review")) return "⭐";
  if (type.startsWith("payment")) return "💰";
  if (type.startsWith("report")) return "🚩";
  return "🔔";
}

export default function NotificationsPage() {
  const [notifs, setNotifs] = useState<NotificationList | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 15;

  const doFetch = () => {
    api.get<NotificationList>("/me/notifications", { params: { page, page_size: PAGE_SIZE } })
      .then(({ data }) => setNotifs(data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { doFetch(); }, [page]);

  const markAllRead = async () => {
    await api.post("/me/notifications/read-all");
    doFetch();
  };

  const markRead = async (id: string) => {
    await api.post(`/notifications/${id}/read`);
    doFetch();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between anim-in">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Notificações</h2>
          <p className="text-gray-500 mt-1">Atualizações sobre sua atividade</p>
        </div>
        {notifs && notifs.unread_count > 0 && (
          <Button variant="outline" size="sm" onClick={markAllRead} className="rounded-full gap-2">
            <Check className="h-3.5 w-3.5" />
            Marcar todas ({notifs.unread_count})
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 skeleton rounded-2xl" />
          ))}
        </div>
      ) : !notifs || notifs.items.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <Bell className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Nenhuma notificação</p>
          <p className="text-sm text-gray-400 mt-1">Você será notificado sobre atividades relevantes</p>
        </div>
      ) : (
        <div className="space-y-2 anim-in-d1">
          {notifs.items.map((n) => (
            <div
              key={n.id}
              className={`bg-white rounded-2xl p-4 ring-1 shadow-sm transition-all ${
                n.read_at
                  ? "ring-black/[0.02] opacity-60"
                  : "ring-primary/10 shadow-primary/5"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-lg flex-shrink-0">{getNotifIcon(n.type)}</span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${n.read_at ? "text-gray-500" : "text-gray-900"}`}>
                    {getNotifMessage(n.type)}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(n.created_at).toLocaleString("pt-BR", {
                      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
                    })}
                  </p>
                </div>
                {!n.read_at && (
                  <button
                    onClick={() => markRead(n.id)}
                    className="p-2 rounded-lg text-gray-400 hover:text-primary hover:bg-gray-50 transition-colors flex-shrink-0"
                    title="Marcar como lida"
                  >
                    <Check className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {notifs && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={notifs.total} onPageChange={setPage} />
      )}
    </div>
  );
}
