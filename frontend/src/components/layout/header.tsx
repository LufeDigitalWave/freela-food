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
    <header className="sticky top-0 z-40 flex h-[72px] items-center gap-4 border-b border-gray-100 bg-white/80 backdrop-blur-xl px-8 md:pl-[292px]">
      <div className="flex-1" />
      <Link
        href="/notifications"
        className="relative p-2.5 rounded-xl hover:bg-gray-50 transition-colors"
      >
        <Bell className="h-5 w-5 text-gray-400" />
        {unread > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white"  >
            {unread}
          </span>
        )}
      </Link>
    </header>
  );
}
