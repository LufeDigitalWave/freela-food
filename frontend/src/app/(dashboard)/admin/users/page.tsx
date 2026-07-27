"use client";

import { useEffect, useState } from "react";
import { Power } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";

interface AdminUser {
  id: string;
  email: string;
  role: string;
  active: boolean;
  created_at: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get<{ items: AdminUser[] }>("/admin/users", { params: { page_size: 50 } })
      .then(({ data }) => setUsers(data.items))
      .catch(() => showToast("Erro ao carregar usuários", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const toggleActive = async (user: AdminUser) => {
    const action = user.active ? "deactivate" : "reactivate";
    if (!confirm(`Confirma ${action === "deactivate" ? "desativar" : "reativar"} ${user.email}?`)) return;

    try {
      await api.post(`/admin/users/${user.id}/${action}`);
      showToast(`Usuário ${action === "deactivate" ? "desativado" : "reativado"}`, "success");
      load();
    } catch {
      showToast("Erro ao atualizar usuário", "error");
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-900">Usuários</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 skeleton rounded-2xl" />
          ))}
        </div>
      ) : users.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Nenhum usuário encontrado.</p>
      ) : (
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-xs uppercase text-gray-400">
              <tr>
                <th className="px-4 py-3 text-left">Email</th>
                <th className="px-4 py-3 text-left">Role</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-3 text-sm">{u.email}</td>
                  <td className="px-4 py-3 text-sm">{u.role}</td>
                  <td className="px-4 py-3">
                    <Badge className={u.active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"}>
                      {u.active ? "Ativo" : "Inativo"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => toggleActive(u)}
                      className="rounded-full"
                    >
                      <Power className="h-3.5 w-3.5" />
                      {u.active ? "Desativar" : "Reativar"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}