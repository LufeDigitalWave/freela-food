"use client";

import { useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";

interface AdminReview {
  id: string;
  reviewer_id: string;
  reviewee_id: string;
  stars: number;
  comment: string | null;
  hidden: boolean;
  created_at: string;
}

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState<AdminReview[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get<{ items: AdminReview[] }>("/admin/reviews", { params: { page_size: 50 } })
      .then(({ data }) => setReviews(data.items || []))
      .catch(() => showToast("Erro ao carregar avaliações", "error"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const toggleVisibility = async (review: AdminReview) => {
    const action = review.hidden ? "unhide" : "hide";
    try {
      await api.post(`/admin/reviews/${review.id}/${action}`);
      showToast(`Avaliação ${action === "hide" ? "ocultada" : "exibida"}`, "success");
      load();
    } catch {
      showToast("Erro ao atualizar avaliação", "error");
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-900">Avaliações</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 skeleton rounded-2xl" />
          ))}
        </div>
      ) : reviews.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Nenhuma avaliação.</p>
      ) : (
        <div className="space-y-3">
          {reviews.map((r) => (
            <div key={r.id} className="bg-white rounded-2xl p-4 ring-1 ring-black/[0.04] shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-900">{"⭐".repeat(r.stars)}</span>
                    {r.hidden && <Badge className="bg-red-50 text-red-600">Oculta</Badge>}
                  </div>
                  {r.comment && (
                    <p className="text-sm text-gray-700 mt-1">{r.comment}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(r.created_at).toLocaleDateString("pt-BR")} · Reviewer #{r.reviewer_id.slice(0, 8)}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => toggleVisibility(r)}
                  className="rounded-full shrink-0"
                >
                  {r.hidden ? <><Eye className="h-3.5 w-3.5" /> Exibir</> : <><EyeOff className="h-3.5 w-3.5" /> Ocultar</>}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}