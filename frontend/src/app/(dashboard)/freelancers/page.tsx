"use client";

import { useState } from "react";
import { MapPin, Search, Star, AlertTriangle, FileCheck, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";
import type { FreelancerSearchList, FreelancerSearchRead } from "@/lib/types";
import { InviteModal } from "@/components/modals/invite-freelancer";

export default function FreelancersPage() {
  const [address, setAddress] = useState("");
  const [radius, setRadius] = useState("10");
  const [results, setResults] = useState<FreelancerSearchList | null>(null);
  const [loading, setLoading] = useState(false);
  const [inviteTarget, setInviteTarget] = useState<FreelancerSearchRead | null>(null);

  const search = async () => {
    if (!address.trim()) return;
    setLoading(true);
    try {
      const geoRes = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=br`,
        { headers: { "Accept-Language": "pt-BR" } }
      );
      const geoData = await geoRes.json();
      if (!geoData.length) {
        showToast("Endereço não encontrado. Tente ser mais específico.", "error");
        setLoading(false);
        return;
      }
      const { lat, lon } = geoData[0];

      const { data } = await api.get<FreelancerSearchList>("/freelancers/search", {
        params: {
          latitude: lat,
          longitude: lon,
          radius_km: radius,
          page_size: 20,
        },
      });
      setResults(data);
    } catch {
      showToast("Erro ao buscar freelancers.", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") search();
  };

  return (
    <div className="space-y-6">
      <div className="anim-in">
        <h2 className="text-2xl md:text-3xl font-bold text-gray-900">Buscar freelancers</h2>
        <p className="text-gray-500 mt-1">Encontre profissionais próximos e envie convites diretos</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
            <div className="space-y-2 md:col-span-2">
              <Label>Endereço, bairro, cidade ou CEP</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Ex: Vila Madalena, São Paulo"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Raio (km)</Label>
              <div className="flex gap-2">
                <Input
                  value={radius}
                  onChange={(e) => setRadius(e.target.value)}
                  type="number"
                  min="1"
                  max="100"
                />
                <Button onClick={search} disabled={loading} className="shrink-0">
                  {loading ? "Buscando..." : "Buscar"}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {results && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            {results.total} freelancer{results.total !== 1 && "s"} encontrado{results.total !== 1 && "s"}
          </p>

          {results.items.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">Nenhum freelancer encontrado nessa região.</p>
              <p className="text-sm text-gray-400 mt-1">Tente aumentar o raio de busca.</p>
            </div>
          ) : (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
              {results.items.map((fl) => (
                <div
                  key={fl.user_id}
                  className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-sm card-lift"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 truncate">{fl.display_name}</p>
                      {fl.bio && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">{fl.bio}</p>
                      )}
                      <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {(fl.distance_m / 1000).toFixed(1)} km
                        </span>
                        {fl.average_rating !== null && (
                          <span className="flex items-center gap-1">
                            <Star className="h-3 w-3 text-amber-500" />
                            {fl.average_rating.toFixed(1)} ({fl.total_reviews})
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <FileCheck className="h-3 w-3" />
                          {fl.completed_contracts_count} contratos
                        </span>
                        {fl.no_show_count > 0 && (
                          <span className="flex items-center gap-1 text-red-500">
                            <AlertTriangle className="h-3 w-3" />
                            {fl.no_show_count} no-show
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      className="rounded-full shrink-0"
                      onClick={() => setInviteTarget(fl)}
                    >
                      <UserPlus className="h-3.5 w-3.5" /> Convidar
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {inviteTarget && (
        <InviteModal
          freelancer={inviteTarget}
          onClose={() => setInviteTarget(null)}
          onSuccess={() => {
            setInviteTarget(null);
            showToast("Convite enviado com sucesso!", "success");
          }}
        />
      )}
    </div>
  );
}
