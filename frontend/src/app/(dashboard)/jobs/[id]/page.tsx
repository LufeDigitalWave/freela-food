"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Clock, DollarSign } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { JobPosting } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [job, setJob] = useState<JobPosting | null>(null);
  const [message, setMessage] = useState("");
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (params.id) {
      api.get<JobPosting>(`/jobs/${params.id}`).then(({ data }) => setJob(data));
    }
  }, [params.id]);

  const handleApply = async () => {
    setApplying(true);
    setError("");
    try {
      await api.post(`/jobs/${params.id}/applications`, {
        message: message || null,
      });
      setApplied(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao candidatar");
    } finally {
      setApplying(false);
    }
  };

  if (!job) {
    return <div className="text-muted-foreground">Carregando...</div>;
  }

  return (
    <div className="max-w-2xl space-y-6">
      <Button variant="ghost" onClick={() => router.back()}>
        ← Voltar
      </Button>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">{job.title}</CardTitle>
            <Badge>{job.status}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {job.description && (
            <p className="text-sm text-muted-foreground">{job.description}</p>
          )}
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {new Date(job.start_at).toLocaleString("pt-BR")} —{" "}
              {new Date(job.end_at).toLocaleString("pt-BR")}
            </div>
            {job.hourly_rate && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-4 w-4" />
                R$ {job.hourly_rate}/h
              </div>
            )}
            {job.total_pay && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-4 w-4" />
                R$ {job.total_pay} (total)
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Formulário de candidatura */}
      {job.status === "open" && !applied && (
        <Card>
          <CardHeader>
            <CardTitle>Candidatar-se</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Mensagem (opcional)</Label>
              <Textarea
                placeholder="Conte por que você é ideal pra essa vaga..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button onClick={handleApply} disabled={applying}>
              {applying ? "Enviando..." : "Enviar candidatura"}
            </Button>
          </CardContent>
        </Card>
      )}

      {applied && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <p className="text-green-800 font-medium">✓ Candidatura enviada com sucesso!</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
