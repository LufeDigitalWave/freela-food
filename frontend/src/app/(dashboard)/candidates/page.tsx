"use client";

import { useEffect, useState } from "react";
import { Check, X, MessageSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface ApplicationItem {
  id: string;
  job_posting_id: string;
  freelancer_id: string;
  status: string;
  message: string | null;
  created_at: string;
}

interface ApplicationListResponse {
  items: ApplicationItem[];
  total: number;
}

export default function CandidatesPage() {
  const [apps, setApps] = useState<ApplicationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch all pending applications for establishment's jobs
    // The backend has GET /v1/jobs/{id}/applications per job
    // For now, we show contracts as placeholder until we add aggregated endpoint
    api.get("/me/contracts", { params: { page_size: 50, status: "scheduled" } })
      .then(({ data }) => {
        setApps([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleAccept = async (appId: string) => {
    try {
      await api.post(`/applications/${appId}/accept`);
      setApps((prev) => prev.filter((a) => a.id !== appId));
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (appId: string) => {
    try {
      await api.post(`/applications/${appId}/reject`);
      setApps((prev) => prev.filter((a) => a.id !== appId));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Candidatos</h2>
        <p className="text-gray-500 mt-1">Candidaturas recebidas nas suas vagas</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 skeleton rounded-2xl" />
          ))}
        </div>
      ) : apps.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Nenhuma candidatura pendente</p>
          <p className="text-sm text-gray-400 mt-1">Publique vagas para receber candidaturas</p>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          {apps.map((app) => (
            <div key={app.id} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Freelancer #{app.freelancer_id.slice(0, 8)}</p>
                  {app.message && (
                    <p className="text-sm text-gray-500 mt-1">"{app.message}"</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(app.created_at).toLocaleDateString("pt-BR")}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="rounded-full text-red-600 hover:bg-red-50 border-red-200"
                    onClick={() => handleReject(app.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    className="rounded-full bg-green-600 hover:bg-green-700"
                    onClick={() => handleAccept(app.id)}
                  >
                    <Check className="h-4 w-4" /> Aceitar
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
