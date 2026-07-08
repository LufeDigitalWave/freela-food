"use client";

import { useEffect, useState } from "react";
import { Star } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ReviewList } from "@/lib/types";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewList | null>(null);

  useEffect(() => {
    api.get<ReviewList>("/me/reviews").then(({ data }) => setReviews(data));
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Minhas avaliações</h2>

      {!reviews ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : reviews.items.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            Você ainda não recebeu avaliações.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {reviews.total} avaliação{reviews.total !== 1 && "ões"} recebida{reviews.total !== 1 && "s"}
          </p>
          {reviews.items.map((r) => (
            <Card key={r.id}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    {Array.from({ length: r.stars }).map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                    {Array.from({ length: 5 - r.stars }).map((_, i) => (
                      <Star key={`e-${i}`} className="h-4 w-4 text-muted-foreground" />
                    ))}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(r.created_at).toLocaleDateString("pt-BR")}
                  </span>
                </div>
                <p className="text-sm mt-2 text-muted-foreground">
                  por {r.reviewer_display_name || "Anônimo"}
                </p>
                {r.comment && <p className="text-sm mt-1">{r.comment}</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
