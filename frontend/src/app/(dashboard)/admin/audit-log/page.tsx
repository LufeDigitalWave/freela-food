"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";

interface AuditEntry {
  id: string;
  actor_id: string;
  action: string;
  entity: string;
  entity_id: string;
  created_at: string;
}

export default function AdminAuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ items: AuditEntry[] }>("/admin/audit-log", { params: { page_size: 50 } })
      .then(({ data }) => setEntries(data.items || []))
      .catch(() => showToast("Erro ao carregar audit log", "error"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-900">Audit Log</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 skeleton rounded-2xl" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Nenhuma entrada no audit log.</p>
      ) : (
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-400">
              <tr>
                <th className="px-4 py-3 text-left">Data</th>
                <th className="px-4 py-3 text-left">Ator</th>
                <th className="px-4 py-3 text-left">Ação</th>
                <th className="px-4 py-3 text-left">Entidade</th>
                <th className="px-4 py-3 text-left">ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {entries.map((e) => (
                <tr key={e.id}>
                  <td className="px-4 py-2.5 text-xs text-gray-400 whitespace-nowrap">
                    {new Date(e.created_at).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="px-4 py-2.5">#{e.actor_id.slice(0, 8)}</td>
                  <td className="px-4 py-2.5 font-medium">{e.action}</td>
                  <td className="px-4 py-2.5">{e.entity}</td>
                  <td className="px-4 py-2.5 text-xs text-gray-400">#{e.entity_id.slice(0, 8)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}