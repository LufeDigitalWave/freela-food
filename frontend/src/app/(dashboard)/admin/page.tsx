"use client";

import { useEffect, useState } from "react";
import { Users, Briefcase, AlertTriangle, CreditCard } from "lucide-react";

import { api } from "@/lib/api";

interface AdminStats {
  total_users: number;
  freelancers: number;
  establishments: number;
  open_reports: number;
  pending_payments: number;
  contracts_total: number;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AdminStats>("/admin/stats")
      .then(({ data }) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-24 skeleton rounded-2xl" />
        ))}
      </div>
    );
  }

  if (!stats) return <div>Não foi possível carregar as estatísticas.</div>;

  const items = [
    { label: "Total usuários", value: stats.total_users, icon: Users, color: "bg-blue-50 text-blue-700" },
    { label: "Freelancers", value: stats.freelancers, icon: Users, color: "bg-orange-50 text-primary" },
    { label: "Estabelecimentos", value: stats.establishments, icon: Briefcase, color: "bg-purple-50 text-purple-700" },
    { label: "Denúncias abertas", value: stats.open_reports, icon: AlertTriangle, color: "bg-red-50 text-red-600" },
    { label: "Pagamentos pendentes", value: stats.pending_payments, icon: CreditCard, color: "bg-amber-50 text-amber-700" },
    { label: "Contratos totais", value: stats.contracts_total, icon: Briefcase, color: "bg-green-50 text-green-700" },
  ];

  return (
    <div className="grid gap-4 grid-cols-2 md:grid-cols-3">
      {items.map((s) => (
        <div key={s.label} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{s.label}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1.5">{s.value}</p>
            </div>
            <div className={`p-2.5 rounded-xl ${s.color}`}>
              <s.icon className="h-5 w-5" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}