"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Star, ArrowLeft, CheckCircle, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import type { ServiceContract, Review, Payment } from "@/lib/types";

const statusLabels: Record<string, string> = {
  scheduled: "Agendado",
  in_progress: "Em andamento",
  completed: "Concluído",
  cancelled: "Cancelado",
};

const statusColors: Record<string, string> = {
  scheduled: "bg-gray-100 text-gray-600",
  in_progress: "bg-blue-50 text-blue-700",
  completed: "bg-green-50 text-green-700",
  cancelled: "bg-red-50 text-red-600",
};

export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [contract, setContract] = useState<ServiceContract | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [reviewSent, setReviewSent] = useState(false);
  const [confirmNotes, setConfirmNotes] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!params.id) return;
    Promise.all([
      api.get<ServiceContract>(`/contracts/${params.id}`),
      api.get<Review[]>(`/contracts/${params.id}/reviews`).catch(() => ({ data: [] })),
      api.get<Payment>(`/contracts/${params.id}/payment`).catch(() => ({ data: null })),
    ]).then(([c, r, p]) => {
      setContract(c.data);
      setReviews(r.data);
      setPayment(p.data);
    }).finally(() => setLoading(false));
  }, [params.id]);

  const handleReview = async () => {
    setReviewing(true);
    setError("");
    try {
      await api.post(`/contracts/${params.id}/reviews`, {
        stars,
        comment: comment || null,
      });
      setReviewSent(true);
      const { data } = await api.get<Review[]>(`/contracts/${params.id}/reviews`);
      setReviews(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao enviar avaliação");
    } finally {
      setReviewing(false);
    }
  };

  const handleConfirmPayment = async () => {
    setConfirming(true);
    setError("");
    try {
      const { data } = await api.post<Payment>(`/contracts/${params.id}/payment/confirm`, {
        notes: confirmNotes || null,
      });
      setPayment(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao confirmar");
    } finally {
      setConfirming(false);
    }
  };

  const handleDispute = async () => {
    try {
      const { data } = await api.post<Payment>(`/contracts/${params.id}/payment/dispute`);
      setPayment(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao disputar");
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl space-y-4">
        <div className="h-8 w-32 skeleton rounded-lg" />
        <div className="h-40 skeleton rounded-2xl" />
        <div className="h-32 skeleton rounded-2xl" />
      </div>
    );
  }

  if (!contract) return <p className="text-gray-400">Contrato não encontrado.</p>;

  const isEstablishment = user?.role === "establishment";
  const isFreelancer = user?.role === "freelancer";

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3 anim-in">
        <button onClick={() => router.back()} className="p-2 rounded-xl hover:bg-gray-50 transition-colors">
          <ArrowLeft className="h-5 w-5 text-gray-400" />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Contrato</h2>
          <p className="text-gray-400 text-sm">#{contract.id.slice(0, 8)}</p>
        </div>
      </div>

      {/* Contract info */}
      <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm anim-in-d1">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Detalhes</h3>
          <Badge className={`${statusColors[contract.status] || ""} rounded-full px-3 text-xs font-semibold`}>
            {statusLabels[contract.status] || contract.status}
          </Badge>
        </div>
        <div className="space-y-2 text-sm text-gray-600">
          <p><span className="font-medium text-gray-900">Período:</span> {new Date(contract.start_at).toLocaleString("pt-BR")} — {new Date(contract.end_at).toLocaleString("pt-BR")}</p>
          <p><span className="font-medium text-gray-900">Valor:</span> {contract.agreed_hourly_rate ? `R$ ${contract.agreed_hourly_rate}/h` : contract.agreed_total_pay ? `R$ ${contract.agreed_total_pay}` : "A combinar"}</p>
          {contract.no_show && (
            <div className="flex items-center gap-2 mt-2 px-3 py-2 bg-red-50 rounded-xl">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              <span className="text-red-600 text-xs font-medium">No-show registrado</span>
            </div>
          )}
        </div>
      </div>

      {/* Payment */}
      {payment && (
        <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm anim-in-d2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Pagamento</h3>
            <Badge className={`rounded-full px-3 text-xs font-semibold ${
              payment.status === "confirmed" ? "bg-green-50 text-green-700" :
              payment.status === "disputed" ? "bg-red-50 text-red-600" :
              "bg-yellow-50 text-yellow-700"
            }`}>
              {payment.status === "confirmed" ? "Confirmado" : payment.status === "disputed" ? "Disputado" : "Pendente"}
            </Badge>
          </div>
          <div className="space-y-2 text-sm text-gray-600">
            <p><span className="font-medium text-gray-900">Valor:</span> R$ {payment.amount}</p>
            {payment.pix_key && <p><span className="font-medium text-gray-900">Pix:</span> {payment.pix_key}</p>}
            {payment.confirmed_at && <p><span className="font-medium text-gray-900">Confirmado em:</span> {new Date(payment.confirmed_at).toLocaleString("pt-BR")}</p>}
            {payment.notes && <p><span className="font-medium text-gray-900">Obs:</span> {payment.notes}</p>}
          </div>

          {/* Establishment: confirm payment */}
          {isEstablishment && payment.status === "pending" && (
            <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
              <Label className="text-sm font-medium">Confirmar pagamento via Pix</Label>
              <Input
                value={confirmNotes}
                onChange={(e) => setConfirmNotes(e.target.value)}
                placeholder="Observação (opcional): comprovante enviado por WhatsApp..."
                className="h-11 rounded-xl bg-muted border-0"
              />
              <Button
                onClick={handleConfirmPayment}
                disabled={confirming}
                className="rounded-full gap-2 bg-green-600 hover:bg-green-700"
              >
                <CheckCircle className="h-4 w-4" />
                {confirming ? "Confirmando..." : "Confirmar que paguei"}
              </Button>
            </div>
          )}

          {/* Freelancer: dispute */}
          {isFreelancer && payment.status === "pending" && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button
                variant="outline"
                onClick={handleDispute}
                className="rounded-full text-red-600 border-red-200 hover:bg-red-50"
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Disputar (não recebi)
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Reviews */}
      <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm anim-in-d3">
        <h3 className="font-semibold text-gray-900 mb-4" style={{ fontFamily: "'Instrument Serif', serif" }}>Avaliações</h3>

        {reviews.length > 0 && (
          <div className="space-y-3 mb-4">
            {reviews.map((r) => (
              <div key={r.id} className="p-3 rounded-xl bg-gray-50">
                <div className="flex items-center gap-2">
                  {Array.from({ length: r.stars }).map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-amber-400 text-amber-400" />
                  ))}
                  <span className="text-xs text-gray-400 ml-2">
                    {r.reviewer_display_name || "Anônimo"}
                  </span>
                </div>
                {r.comment && <p className="text-sm text-gray-600 mt-1.5">{r.comment}</p>}
              </div>
            ))}
          </div>
        )}

        {/* Review form */}
        {contract.status === "completed" && !reviewSent && (
          <div className="space-y-3 pt-3 border-t border-gray-100">
            <Label className="text-sm font-medium">Sua avaliação</Label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <button key={s} type="button" onClick={() => setStars(s)}>
                  <Star className={`h-7 w-7 cursor-pointer transition-colors ${
                    s <= stars ? "fill-amber-400 text-amber-400" : "text-gray-200"
                  }`} />
                </button>
              ))}
            </div>
            <Textarea
              placeholder="Comentário (opcional)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={2}
              className="rounded-xl bg-muted border-0 resize-none"
            />
            {error && (
              <div className="px-3 py-2 rounded-xl bg-red-50 border border-red-100">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
            <Button onClick={handleReview} disabled={reviewing} className="rounded-full">
              {reviewing ? "Enviando..." : "Enviar avaliação"}
            </Button>
          </div>
        )}

        {reviewSent && (
          <div className="px-4 py-3 rounded-xl bg-green-50 border border-green-100">
            <p className="text-sm text-green-700">✓ Avaliação enviada!</p>
          </div>
        )}

        {contract.status !== "completed" && reviews.length === 0 && (
          <p className="text-sm text-gray-400">Avaliações disponíveis após conclusão do contrato.</p>
        )}
      </div>
    </div>
  );
}
