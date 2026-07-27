"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle } from "lucide-react";

import { api } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";

export function ProfileBanner() {
  const { user } = useAuth();
  const [incomplete, setIncomplete] = useState(false);

  useEffect(() => {
    if (!user) return;
    api
      .get("/me")
      .then(({ data }) => {
        const profile =
          user.role === "freelancer"
            ? data.freelancer_profile
            : data.establishment_profile;
        if (!profile || !profile.display_name) {
          setIncomplete(true);
        }
      })
      .catch(() => {});
  }, [user]);

  if (!incomplete) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-center gap-3">
      <AlertCircle className="h-5 w-5 text-amber-600 shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-amber-800">Complete seu perfil</p>
        <p className="text-xs text-amber-600 mt-0.5">
          Preencha suas informações para aparecer nas buscas e receber convites.
        </p>
      </div>
      <Link
        href="/onboarding"
        className="px-3 py-1.5 rounded-full bg-amber-600 text-white text-xs font-medium hover:bg-amber-700 transition-colors shrink-0"
      >
        Completar
      </Link>
    </div>
  );
}
