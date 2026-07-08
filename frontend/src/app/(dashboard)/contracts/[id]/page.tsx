"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { ServiceContract, Review, Payment } from "@/lib/types";

export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [contract, setContract] = useState<ServiceContract | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [reviewSent, setReviewSent] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!params.id) return;
    api.get<ServiceContract>(`/contracts/${params.id}`).then(({ data }) => setContract(data));
    api.get<Review[]>(`/contracts/${params.id}/reviews`).then(({ data }) => setReviews(data)).catch(() => {});
    api.get<Payment>(`/contracts/${params.id}/payment`).then(({ data }) => setPayment(data)).catch(() => {});
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
      // Refresh reviews
      const { data } = await api.get<Review[]>(`/contracts/${params.id}/reviews`);
      setReviews(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao enviar avaliação");
    } finally {
      setReviewing(false);
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

  if (!contract) return <div className="text-muted-foreground">Carregando...</div>;

  return (
    <div className="max-w-2xl space-y-6">
      <Button variant="ghost" onClick={() => router.back()}>← Voltar</Button>

      {/* Contrato */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Contrato</CardTitle>
            <Badge>{contract.status}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p><strong>Período:</strong> {new Date(contract.start_at).toLocaleString("pt-BR")} — {new Date(contract.end_at).toLocaleString("pt-BR")}</p>
          <p><strong>Valor:</strong> {contract.agreed_hourly_rate ? `R$ ${contract.agreed_hourly_rate}/h` : contract.agreed_total_pay ? `R$ ${contract.agreed_total_pay}` : "—"}</p>
          {contract.no_show && <Badge variant="destructive">No-show</Badge>}
        </CardContent>
      </Card>

      {/* Payment */}
      {payment && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Pagamento</CardTitle>
              <Badge variant={payment.status === "confirmed" ? "default" : payment.status === "disputed" ? "destructive" : "secondary"}>
                {payment.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p><strong>Valor:</strong> R$ {payment.amount}</p>
            {payment.pix_key && <p><strong>Pix:</strong> {payment.pix_key}</p>}
            {payment.confirmed_at && <p><strong>Confirmado em:</strong> {new Date(payment.confirmed_at).toLocaleString("pt-BR")}</p>}
            {payment.status === "pending" && (
              <Button variant="destructive" size="sm" onClick={handleDispute}>
                Disputar (não recebi)
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Reviews */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Avaliações</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {reviews.length === 0 && !reviewSent ? (
            <p className="text-sm text-muted-foreground">Nenhuma avaliação ainda.</p>
          ) : (
            reviews.map((r) => (
              <div key={r.id} className="border-b pb-3">
                <div className="flex items-center gap-2">
                  {Array.from({ length: r.stars }).map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  ))}
                  <span className="text-xs text-muted-foreground">
                    {r.reviewer_display_name || "Anônimo"}
                  </span>
                </div>
                {r.comment && <p className="text-sm mt-1">{r.comment}</p>}
              </div>
            ))
          )}

          {/* Form review — só se contrato completed e user não avaliou ainda */}
          {contract.status === "completed" && !reviewSent && (
            <div className="space-y-3 pt-4 border-t">
              <Label>Sua avaliação</Label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((s) => (
                  <button key={s} type="button" onClick={() => setStars(s)}>
                    <Star
                      className={`h-6 w-6 cursor-pointer ${
                        s <= stars ? "fill-yellow-400 text-yellow-400" : "text-muted-foreground"
                      }`}
                    />
                  </button>
                ))}
              </div>
              <Textarea
                placeholder="Comentário (opcional)"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={2}
              />
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button onClick={handleReview} disabled={reviewing} size="sm">
                {reviewing ? "Enviando..." : "Enviar avaliação"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
