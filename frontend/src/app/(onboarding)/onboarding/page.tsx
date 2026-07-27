"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";
import { useAuth } from "@/hooks/use-auth";

const STEPS_FREELANCER = ["Dados básicos", "Localização", "Pagamento"];
const STEPS_ESTABLISHMENT = ["Dados do estabelecimento", "Endereço"];

export default function OnboardingPage() {
  const { user, loading, fetchMe } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Freelancer fields
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [phone, setPhone] = useState("");
  const [pixKey, setPixKey] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [radiusKm, setRadiusKm] = useState("10");

  // Establishment fields
  const [estName, setEstName] = useState("");
  const [estPhone, setEstPhone] = useState("");
  const [estAddress, setEstAddress] = useState("");
  const [estCity, setEstCity] = useState("");
  const [estState, setEstState] = useState("");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) return null;

  const isFreelancer = user.role === "freelancer";
  const steps = isFreelancer ? STEPS_FREELANCER : STEPS_ESTABLISHMENT;
  const totalSteps = steps.length;

  const handleNext = () => {
    if (step < totalSteps - 1) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      if (isFreelancer) {
        const geoRes = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(addressLine)}&format=json&limit=1&countrycodes=br`
        );
        const geoData = await geoRes.json();
        const lat = geoData[0]?.lat || null;
        const lng = geoData[0]?.lon || null;

        await api.post("/me/freelancer-profile", {
          display_name: displayName,
          bio: bio || null,
          phone: phone || null,
          pix_key: pixKey || null,
          latitude: lat ? parseFloat(lat) : null,
          longitude: lng ? parseFloat(lng) : null,
          service_radius_km: parseInt(radiusKm) || 10,
        });
      } else {
        const geoRes = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(`${estAddress}, ${estCity}, ${estState}`)}&format=json&limit=1&countrycodes=br`
        );
        const geoData = await geoRes.json();
        const lat = geoData[0]?.lat || null;
        const lng = geoData[0]?.lon || null;

        await api.post("/me/establishment-profile", {
          display_name: estName,
          phone: estPhone || null,
          address_line: estAddress || null,
          city: estCity || null,
          state: estState || null,
          latitude: lat ? parseFloat(lat) : null,
          longitude: lng ? parseFloat(lng) : null,
        });
      }

      await fetchMe();
      showToast("Perfil criado! Bem-vindo ao freela-food.", "success");
      router.push("/");
    } catch {
      showToast("Erro ao salvar perfil. Tente novamente.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm">
      <div className="flex items-center gap-2 mb-6">
        {steps.map((s, i) => (
          <div key={s} className="flex-1">
            <div
              className={`h-1.5 rounded-full transition-colors ${
                i <= step ? "bg-primary" : "bg-gray-200"
              }`}
            />
            <p className={`text-[10px] mt-1 ${i <= step ? "text-primary font-medium" : "text-gray-400"}`}>
              {s}
            </p>
          </div>
        ))}
      </div>

      {isFreelancer && step === 0 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Nome de exibição *</Label>
            <Input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Como quer ser chamado"
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>
          <div className="space-y-2">
            <Label>Bio</Label>
            <Textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Conte sobre sua experiência..."
              rows={3}
              className="rounded-xl bg-muted border-0 resize-none"
            />
          </div>
          <div className="space-y-2">
            <Label>Telefone</Label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="(11) 99999-9999"
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>
        </div>
      )}

      {isFreelancer && step === 1 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Endereço ou bairro *</Label>
            <Input
              value={addressLine}
              onChange={(e) => setAddressLine(e.target.value)}
              placeholder="Bairro, cidade ou CEP"
              className="h-11 rounded-xl bg-muted border-0"
            />
            <p className="text-xs text-gray-400">Usamos para localizar vagas perto de você</p>
          </div>
          <div className="space-y-2">
            <Label>Raio de atuação (km)</Label>
            <Input
              type="number"
              min="1"
              max="100"
              value={radiusKm}
              onChange={(e) => setRadiusKm(e.target.value)}
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>
        </div>
      )}

      {isFreelancer && step === 2 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Chave Pix</Label>
            <Input
              value={pixKey}
              onChange={(e) => setPixKey(e.target.value)}
              placeholder="CPF, email ou chave aleatória"
              className="h-11 rounded-xl bg-muted border-0"
            />
            <p className="text-xs text-gray-400">Necessária para receber pagamentos</p>
          </div>
        </div>
      )}

      {!isFreelancer && step === 0 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Nome do estabelecimento *</Label>
            <Input
              value={estName}
              onChange={(e) => setEstName(e.target.value)}
              placeholder="Bar do Zé"
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>
          <div className="space-y-2">
            <Label>Telefone</Label>
            <Input
              value={estPhone}
              onChange={(e) => setEstPhone(e.target.value)}
              placeholder="(11) 99999-9999"
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>
        </div>
      )}

      {!isFreelancer && step === 1 && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Endereço *</Label>
            <Input
              value={estAddress}
              onChange={(e) => setEstAddress(e.target.value)}
              placeholder="Rua Augusta, 1234"
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Cidade</Label>
              <Input
                value={estCity}
                onChange={(e) => setEstCity(e.target.value)}
                placeholder="São Paulo"
                className="h-11 rounded-xl bg-muted border-0"
              />
            </div>
            <div className="space-y-2">
              <Label>Estado</Label>
              <Input
                value={estState}
                onChange={(e) => setEstState(e.target.value)}
                placeholder="SP"
                maxLength={2}
                className="h-11 rounded-xl bg-muted border-0"
              />
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-3 mt-6">
        {step > 0 && (
          <Button type="button" variant="outline" onClick={handleBack} className="flex-1 rounded-full">
            Voltar
          </Button>
        )}
        {step < totalSteps - 1 ? (
          <Button type="button" onClick={handleNext} className="flex-1 rounded-full">
            Próximo
          </Button>
        ) : (
          <Button type="button" onClick={handleSubmit} disabled={submitting} className="flex-1 rounded-full">
            {submitting ? "Salvando..." : "Concluir"}
          </Button>
        )}
      </div>

      <div className="text-center mt-4">
        <button
          type="button"
          onClick={() => router.push("/")}
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
        >
          Pular por agora
        </button>
      </div>
    </div>
  );
}
