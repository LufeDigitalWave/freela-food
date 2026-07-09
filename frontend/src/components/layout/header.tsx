"use client";

import { Bell } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export function Header() {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    api
      .get<{ unread: number }>("/me/notifications/count")
      .then(({ data }) => setUnread(data.unread))
      .catch(() => {});
  }, []);

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border/30 backdrop-blur-xl bg-background/80 px-6 md:pl-72">
      <div className="flex-1" />
      <div className="flex items-center gap-3">
        <Link
          href="/notifications"
          className="relative p-2 rounded-lg hover:bg-secondary/60 transition-colors"
        >
          <Bell className="h-5 w-5 text-muted-foreground" />
          {unread > 0 && (
            <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
              {unread}
            </span>
          )}
        </Link>
      </div>
    </header>
  );
}
