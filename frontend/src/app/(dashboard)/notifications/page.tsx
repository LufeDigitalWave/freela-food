"use client";

import { useEffect, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { NotificationList } from "@/lib/types";

export default function NotificationsPage() {
  const [notifs, setNotifs] = useState<NotificationList | null>(null);

  const fetch = () => {
    api.get<NotificationList>("/me/notifications?page_size=50").then(({ data }) => setNotifs(data));
  };

  useEffect(() => { fetch(); }, []);

  const markAllRead = async () => {
    await api.post("/me/notifications/read-all");
    fetch();
  };

  const markRead = async (id: string) => {
    await api.post(`/notifications/${id}/read`);
    fetch();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Notificações</h2>
        {notifs && notifs.unread_count > 0 && (
          <Button variant="outline" size="sm" onClick={markAllRead}>
            Marcar todas como lidas ({notifs.unread_count})
          </Button>
        )}
      </div>

      {!notifs ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : notifs.items.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            Nenhuma notificação.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {notifs.items.map((n) => (
            <Card
              key={n.id}
              className={n.read_at ? "opacity-60" : "border-primary/20"}
            >
              <CardContent className="pt-4 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      {n.type.replace(/\./g, " → ")}
                    </span>
                    {!n.read_at && <Badge variant="secondary" className="text-[10px]">nova</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(n.created_at).toLocaleString("pt-BR")}
                  </p>
                </div>
                {!n.read_at && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markRead(n.id)}
                  >
                    Marcar lida
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
