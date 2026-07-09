"use client";

import { useEffect, useState } from "react";
import { Star } from "lucide-react";

import { api } from "@/lib/api";
import type { ReviewList } from "@/lib/types";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ReviewList>("/me/reviews")
      .then(({ data }) => setReviews(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Minhas avaliações</h2>
        <p className="text-gray-500 mt-1">Avaliações recebidas de contratantes</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 skeleton rounded-2xl" />
          ))}
        </div>
      ) : !reviews || reviews.items.length === 0 ? (
        <div className="text-center py-16 anim-in-d1">
          <div className="w-16 h-16 rounded-2xl bg-gray-50 flex items-center justify-center mx-auto mb-4">
            <Star className="h-7 w-7 text-gray-300" />
          </div>
          <p className="text-gray-500">Você ainda não recebeu avaliações</p>
          <p className="text-sm text-gray-400 mt-1">Conclua contratos pra receber feedback</p>
        </div>
      ) : (
        <div className="space-y-3 anim-in-d1">
          <p className="text-sm text-gray-400">
            {reviews.total} avaliação{reviews.total !== 1 && "ões"} recebida{reviews.total !== 1 && "s"}
          </p>
          {reviews.items.map((r) => (
            <div key={r.id} className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star
                      key={i}
                      className={`h-4 w-4 ${
                        i < r.stars ? "fill-amber-400 text-amber-400" : "text-gray-200"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(r.created_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                por <span className="font-medium text-gray-700">{r.reviewer_display_name || "Anônimo"}</span>
              </p>
              {r.comment && (
                <p className="text-sm text-gray-600 mt-2 italic">"{r.comment}"</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
