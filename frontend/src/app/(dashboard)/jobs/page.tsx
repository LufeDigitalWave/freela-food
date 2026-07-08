"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MapPin, Clock, DollarSign, Search } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { JobSearchResponse } from "@/lib/types";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSearchResponse | null>(null);
  const [address, setAddress] = useState("");
  const [radius, setRadius] = useState("10");
  const [loading, setLoading] = useState(false);
  const [geocoding, setGeocoding] = useState(false);
  const [locationName, setLocationName] = useState("");

  const geocodeAndSearch = async () => {
    if (!address.trim()) return;
    setGeocoding(true);
    setLoading(true);
    try {
      // Geocode via Nominatim (OpenStreetMap — gratuito)
      const geoRes = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=br`,
        { headers: { "Accept-Language": "pt-BR" } }
      );
      const geoData = await geoRes.json();
      if (!geoData.length) {
        alert("Endereço não encontrado. Tente ser mais específico.");
        setLoading(false);
        setGeocoding(false);
        return;
      }
      const { lat, lon, display_name } = geoData[0];
      setLocationName(display_name);
      setGeocoding(false);

      // Buscar vagas
      const { data } = await api.get<JobSearchResponse>("/jobs/search", {
        params: {
          latitude: lat,
          longitude: lon,
          radius_km: radius,
          only_open: true,
          future_only: true,
        },
      });
      setJobs(data);
    } catch (err) {
      console.error(err);
      alert("Erro ao buscar. Tente novamente.");
    } finally {
      setLoading(false);
      setGeocoding(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") geocodeAndSearch();
  };

  // Tentar geolocation do browser como sugestão
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          try {
            const res = await fetch(
              `https://nominatim.openstreetmap.org/reverse?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&format=json`,
              { headers: { "Accept-Language": "pt-BR" } }
            );
            const data = await res.json();
            if (data.address) {
              const parts = [data.address.suburb, data.address.city, data.address.state].filter(Boolean);
              setAddress(parts.join(", "));
            }
          } catch {}
        },
        () => {}
      );
    }
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Buscar vagas</h2>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-3">
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
                <Button onClick={geocodeAndSearch} disabled={loading} className="shrink-0">
                  {geocoding ? "Localizando..." : loading ? "Buscando..." : "Buscar"}
                </Button>
              </div>
            </div>
          </div>
          {locationName && (
            <p className="text-xs text-muted-foreground mt-2">
              📍 {locationName}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Resultados */}
      {jobs && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {jobs.total} vaga{jobs.total !== 1 && "s"} encontrada{jobs.total !== 1 && "s"}
          </p>
          {jobs.items.map((job) => (
            <Card key={job.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{job.title}</CardTitle>
                  <Badge>{job.status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {new Date(job.start_at).toLocaleDateString("pt-BR")} —{" "}
                    {new Date(job.end_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  {job.hourly_rate && (
                    <div className="flex items-center gap-1">
                      <DollarSign className="h-3.5 w-3.5" />
                      R$ {job.hourly_rate}/h
                    </div>
                  )}
                  {job.distance_m !== undefined && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" />
                      {(job.distance_m / 1000).toFixed(1)} km
                    </div>
                  )}
                </div>
                <div className="mt-3">
                  <Link href={`/jobs/${job.id}`}>
                    <Button size="sm" variant="outline">Ver detalhes</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
