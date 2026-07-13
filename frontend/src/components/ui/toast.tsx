"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

interface Toast {
  id: string;
  message: string;
  type: "error" | "success" | "info";
}

let addToastFn: ((message: string, type?: "error" | "success" | "info") => void) | null = null;

export function showToast(message: string, type: "error" | "success" | "info" = "error") {
  addToastFn?.(message, type);
}

export function ToastProvider() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    addToastFn = (message, type = "error") => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    };
    return () => { addToastFn = null; };
  }, []);

  if (toasts.length === 0) return null;

  const colors = {
    error: "bg-red-50 border-red-200 text-red-700",
    success: "bg-green-50 border-green-200 text-green-700",
    info: "bg-blue-50 border-blue-200 text-blue-700",
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 space-y-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg ${colors[t.type]} animate-[fadeInUp_0.3s_ease-out]`}
        >
          <p className="text-sm font-medium flex-1">{t.message}</p>
          <button
            onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
            className="opacity-60 hover:opacity-100"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
