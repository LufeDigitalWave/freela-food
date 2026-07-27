"use client";

import { useEffect, useState } from "react";
import { Check, X, MessageSquare, Briefcase } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";
import type { Application, JobPosting } from "@/lib/types";

interface JobWithApplications {
  job: JobPosting;
  applications: Application[];
}

export default function CandidatesPage() {
  const [jobsWithApps, setJobsWithApps] = useState<JobWithApplications[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data: jobsData } = await api.get<{ items: JobPosting[] }>("/jobs", {
          params: { page_size: 50 },
        });
        const jobs = jobsData.items || [];

        const results = await Promise.all(
          jobs
            .filter((j) => j.status === "open" || j.status === "filled")
            .map(async (job) => {
              try {
                const { data } = await api.get<{ items: Application[] }>(
                  `/jobs/${job.id}/applications`,
                  { params: { page_size: 50 } }
                );
                return { job, applications: data.items || [] };
              } catch {
                return { job, applications: [] };
              }
            })
        );

        setJobsWithApps(results.filter((r) => r.applications.length > 0));
      } catch {
        showToast("Erro ao carregar candidatos", "error");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const handleAccept = async (appId: string, jobId: string) => {
    try {
      await api.post(`/applications/${appId}/accept`);
      showToast("Candidato aceito! Contrato criado.", "success");
      setJobsWithApps((prev) =>
        prev.map((jwa) =>
          jwa.job.id === jobId
            ? {
                ...jwa,
                job: { ...jwa.job, status: "filled" as const },
                applications: jwa.applications.map((a) =>
                  a.id === appId
                    ? { ...a, status: "accepted" as const }
                    : a.status === "pending"
                    ? { ...a, status: "rejected" as const }
                    : a
                ),
              }
            : jwa
        )
      );
    } catch {
      showToast("Erro ao aceitar candidato", "error");
    }
  };

  const handleReject = async (appId: string, jobId: string) => {
    try {
      await api.post(`/applications/${appId}/reject`);
      showToast("Candidatura rejeitada", "success");
      setJobsWithApps((prev) =>
        prev.map((jwa) =>
          jwa.job.id === jobId
            ? {
                ...jwa,
                applications: jwa.applications.map((a) =>
                  a.id === appId ? { ...a, status: "rejected" as const } : a
                ),
              }
            : jwa
        )
      );
    } catch {
      showToast("Erro ao rejeitar candidatura", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Candidatos</h2>
        <p className="text-gray-500 mt-1">Candidaturas recebidas nas suas vagas</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 skeleton rounded-2xl" />
          ))}
        </div>
      ) : jobsWithApps.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Nenhuma candidatura pendente</p>
          <p className="text-sm text-gray-400 mt-1">Publique vagas para receber candidaturas</p>
        </div>
      ) : (
        <div className="space-y-6 anim-in-d1">
          {jobsWithApps.map(({ job, applications }) => (
            <div key={job.id} className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-50 flex items-center gap-3">
                <Briefcase className="h-4 w-4 text-gray-400" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {job.title || `Vaga #${job.id.slice(0, 8)}`}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(job.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                    {" · "}
                    {applications.length} candidato{applications.length !== 1 && "s"}
                  </p>
                </div>
                <Badge className={`rounded-full text-[11px] font-semibold ${
                  job.status === "open" ? "bg-green-50 text-green-700" : "bg-blue-50 text-blue-700"
                }`}>
                  {job.status === "open" ? "Aberta" : "Preenchida"}
                </Badge>
              </div>

              <div className="divide-y divide-gray-50">
                {applications.map((app) => (
                  <div key={app.id} className="px-5 py-3 flex items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        Freelancer #{app.freelancer_id.slice(0, 8)}
                      </p>
                      {app.message && (
                        <p className="text-xs text-gray-500 truncate mt-0.5">"{app.message}"</p>
                      )}
                      <p className="text-xs text-gray-400 mt-0.5">
                        {new Date(app.created_at).toLocaleDateString("pt-BR")}
                        {app.status !== "pending" && (
                          <span className="ml-2">
                            ·{" "}
                            {app.status === "accepted" ? "✓ Aceito" : app.status === "rejected" ? "✗ Rejeitado" : app.status}
                          </span>
                        )}
                      </p>
                    </div>
                    {app.status === "pending" && (
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-full text-red-600 hover:bg-red-50 border-red-200"
                          onClick={() => handleReject(app.id, job.id)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          className="rounded-full bg-green-600 hover:bg-green-700"
                          onClick={() => handleAccept(app.id, job.id)}
                        >
                          <Check className="h-4 w-4" /> Aceitar
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
