"use client";

import { Bell, LogOut } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export function Header() {
  const { user, logout } = useAuth();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    api
      .get<{ unread: number }>("/me/notifications/count")
      .then(({ data }) => setUnread(data.unread))
      .catch(() => {});
  }, []);

  return (
    <header className="sticky top-0 z-40 flex h-14 items-center gap-4 border-b bg-background px-6 md:pl-72">
      <div className="flex-1" />
      <div className="flex items-center gap-4">
        <div className="relative">
          <Bell className="h-5 w-5 text-muted-foreground" />
          {unread > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] text-destructive-foreground">
              {unread}
            </span>
          )}
        </div>
        <span className="text-sm text-muted-foreground">{user?.email}</span>
        <Button variant="ghost" size="icon" onClick={logout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
