"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, MapPin, Clock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface MyJob {
  id: string;
  title: string;
  status: string;
  start_at: string;
  end_at: string;
  hourly_rate: string | null;
  total_pay: string | null;
  created_at: string;
}

interface MyJobsResponse {
  items: MyJob[];
  total: number;
  page: number;
  page_size: number;
}

const statusConfig: Record<string, { label: string; color: string }> = {
  open: { label: "Aberta", color: "bg-green-50 text-green-700" },
  filled: { label: "Preenchida", color: "bg-blue-50 text-blue-700" },
  completed: { label: "Concluída", color: "bg-gray-100 text-gray-600" },
  cancelled: { label: "Cancelada", color: "bg-red-50 text-red-600" },
  draft: { label: "Rascunho", color: "bg-yellow-50 text-yellow-700" },
};

export default function MyJobsPage() {
  const [jobs, setJobs] = useState<MyJobsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<MyJobsResponse>("/jobs", { params: { page_size: 50 } })
      .then(({ data }) => setJobs(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between anim-in">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Minhas vagas</h2>
          <p className="text-gray-500 mt-1">Gerencie suas vagas publicadas</p>
        </div>
        <Link href="/jobs/new">
          <Button className="rounded-full gap-2 h-11 px-5">
            <Plus className="h-4 w-4" /> Nova vaga
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 skeleton rounded-2xl" />
          ))}
        </div>
      ) : !jobs || jobs.items.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <MapPin className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500 mb-4">Você ainda não publicou nenhuma vaga</p>
          <Link href="/jobs/new">
            <Button className="rounded-full">Criar primeira vaga</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          {jobs.items.map((job) => {
            const cfg = statusConfig[job.status] || statusConfig.open;
            return (
              <Link key={job.id} href={`/jobs/${job.id}`}>
                <div className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-900">{job.title}</h3>
                      <div className="flex items-center gap-3 mt-1.5 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          {new Date(job.start_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })}
                        </span>
                        {job.hourly_rate && <span>R$ {job.hourly_rate}/h</span>}
                        {job.total_pay && <span>R$ {job.total_pay}</span>}
                      </div>
                    </div>
                    <Badge className={`${cfg.color} rounded-full px-2.5 text-[11px] font-semibold`}>
                      {cfg.label}
                    </Badge>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
