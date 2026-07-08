"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { MapPin, Clock, DollarSign } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { JobSearchResponse } from "@/lib/types";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSearchResponse | null>(null);
  const [lat, setLat] = useState("-23.55");
  const [lng, setLng] = useState("-46.63");
  const [radius, setRadius] = useState("10");
  const [loading, setLoading] = useState(false);

  const search = async () => {
    setLoading(true);
    try {
      const { data } = await api.get<JobSearchResponse>("/jobs/search", {
        params: {
          latitude: lat,
          longitude: lng,
          radius_km: radius,
          only_open: true,
          future_only: true,
        },
      });
      setJobs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Tentar geolocation do browser
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(pos.coords.latitude.toFixed(4));
          setLng(pos.coords.longitude.toFixed(4));
        },
        () => {} // silenciar erro
      );
    }
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Buscar vagas</h2>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label>Latitude</Label>
              <Input value={lat} onChange={(e) => setLat(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Longitude</Label>
              <Input value={lng} onChange={(e) => setLng(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Raio (km)</Label>
              <Input value={radius} onChange={(e) => setRadius(e.target.value)} />
            </div>
            <div className="flex items-end">
              <Button onClick={search} disabled={loading} className="w-full">
                {loading ? "Buscando..." : "Buscar"}
              </Button>
            </div>
          </div>
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
