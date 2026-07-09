"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [address, setAddress] = useState("");
  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("08:00");
  const [endTime, setEndTime] = useState("12:00");
  const [hourlyRate, setHourlyRate] = useState("");
  const [totalPay, setTotalPay] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Geocode address
      const geoRes = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1&countrycodes=br`,
        { headers: { "Accept-Language": "pt-BR" } }
      );
      const geoData = await geoRes.json();
      if (!geoData.length) {
        setError("Endereço não encontrado. Seja mais específico.");
        setLoading(false);
        return;
      }
      const { lat, lon } = geoData[0];

      // Build datetimes
      const start_at = `${startDate}T${startTime}:00`;
      const endDate = startDate; // same day by default
      const end_at = `${endDate}T${endTime}:00`;

      await api.post("/jobs", {
        title,
        description: description || null,
        latitude: parseFloat(lat),
        longitude: parseFloat(lon),
        start_at,
        end_at,
        hourly_rate: hourlyRate ? parseFloat(hourlyRate) : null,
        total_pay: totalPay ? parseFloat(totalPay) : null,
      });

      router.push("/jobs/mine");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao criar vaga");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-3 anim-in">
        <button onClick={() => router.back()} className="p-2 rounded-xl hover:bg-gray-50 transition-colors">
          <ArrowLeft className="h-5 w-5 text-gray-400" />
        </button>
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Criar vaga</h2>
          <p className="text-gray-500 mt-1">Publique uma oportunidade pra freelancers</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 anim-in-d1">
        <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm space-y-5">
          <div className="space-y-2">
            <Label className="text-sm font-medium">Título da vaga *</Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Garçom para evento corporativo"
              required
              className="h-12 rounded-xl bg-muted border-0"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium">Descrição</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detalhes sobre o serviço, dress code, experiência necessária..."
              rows={3}
              className="rounded-xl bg-muted border-0 resize-none"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-sm font-medium">Local do serviço *</Label>
            <Input
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Endereço, bairro ou CEP"
              required
              className="h-12 rounded-xl bg-muted border-0"
            />
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm space-y-5">
          <h3 className="font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Data e horário</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Data *</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="h-12 rounded-xl bg-muted border-0"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Início *</Label>
              <Input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                className="h-12 rounded-xl bg-muted border-0"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Fim *</Label>
              <Input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
                className="h-12 rounded-xl bg-muted border-0"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm space-y-5">
          <h3 className="font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Remuneração</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Valor por hora (R$)</Label>
              <Input
                type="number"
                step="0.01"
                value={hourlyRate}
                onChange={(e) => setHourlyRate(e.target.value)}
                placeholder="30.00"
                className="h-12 rounded-xl bg-muted border-0"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Ou valor total (R$)</Label>
              <Input
                type="number"
                step="0.01"
                value={totalPay}
                onChange={(e) => setTotalPay(e.target.value)}
                placeholder="200.00"
                className="h-12 rounded-xl bg-muted border-0"
              />
            </div>
          </div>
          <p className="text-xs text-gray-400">Preencha um dos dois campos</p>
        </div>

        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button
          type="submit"
          className="w-full h-12 rounded-full font-semibold text-base"
          disabled={loading}
        >
          {loading ? "Publicando..." : "Publicar vaga"}
        </Button>
      </form>
    </div>
  );
}
