"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/use-auth";
import type { FreelancerProfile } from "@/lib/types";

interface EstablishmentProfile {
  user_id: string;
  business_name: string;
  address_line: string | null;
  neighborhood: string | null;
  city: string | null;
  state: string | null;
  cep: string | null;
  phone: string | null;
  avatar_url: string | null;
}

export default function ProfilePage() {
  const { user } = useAuth();

  if (user?.role === "establishment") {
    return <EstablishmentProfileForm />;
  }
  return <FreelancerProfileForm />;
}

// ─── Freelancer Profile ──────────────────────────────────────────────────────

function FreelancerProfileForm() {
  const [profile, setProfile] = useState<FreelancerProfile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [phone, setPhone] = useState("");
  const [pixKey, setPixKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ freelancer_profile: FreelancerProfile | null }>("/me").then(({ data }) => {
      const p = data.freelancer_profile;
      if (p) {
        setProfile(p);
        setDisplayName(p.display_name || "");
        setBio(p.bio || "");
        setPhone(p.phone || "");
        setPixKey(p.pix_key || "");
      }
    }).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);
    try {
      if (profile) {
        await api.patch("/me/freelancer-profile", {
          display_name: displayName,
          bio: bio || null,
          phone: phone || null,
          pix_key: pixKey || null,
        });
      } else {
        await api.post("/me/freelancer-profile", {
          display_name: displayName,
          bio: bio || null,
          phone: phone || null,
          pix_key: pixKey || null,
        });
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl space-y-4">
        <div className="h-8 w-48 skeleton rounded-lg" />
        <div className="h-64 skeleton rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Meu perfil</h2>
        <p className="text-gray-500 mt-1">Informações visíveis pra estabelecimentos</p>
      </div>

      {/* Stats inline */}
      {profile && (
        <div className="flex gap-6 anim-in-d1">
          {[
            { label: "Contratos", value: profile.completed_contracts_count },
            { label: "Rating", value: profile.average_rating ? profile.average_rating.toFixed(1) : "—" },
            { label: "Reviews", value: profile.total_reviews },
            { label: "No-shows", value: profile.no_show_count },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-2xl font-bold text-gray-900">{s.value}</p>
              <p className="text-xs text-gray-400">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm space-y-5 anim-in-d2">
        <div className="space-y-2">
          <Label className="text-sm font-medium">Nome de exibição *</Label>
          <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Como quer ser chamado" className="h-12 rounded-xl bg-muted border-0" />
        </div>
        <div className="space-y-2">
          <Label className="text-sm font-medium">Bio</Label>
          <Textarea value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Conte sobre sua experiência..." rows={3} className="rounded-xl bg-muted border-0 resize-none" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-sm font-medium">Telefone</Label>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="(11) 99999-9999" className="h-12 rounded-xl bg-muted border-0" />
          </div>
          <div className="space-y-2">
            <Label className="text-sm font-medium">Chave Pix</Label>
            <Input value={pixKey} onChange={(e) => setPixKey(e.target.value)} placeholder="CPF, email ou chave" className="h-12 rounded-xl bg-muted border-0" />
          </div>
        </div>

        {success && (
          <div className="px-4 py-3 rounded-xl bg-green-50 border border-green-100">
            <p className="text-sm text-green-700">✓ Perfil salvo com sucesso!</p>
          </div>
        )}

        <Button onClick={handleSave} disabled={saving} className="rounded-full h-11 px-6">
          {saving ? "Salvando..." : "Salvar perfil"}
        </Button>
      </div>
    </div>
  );
}

// ─── Establishment Profile ───────────────────────────────────────────────────

function EstablishmentProfileForm() {
  const [businessName, setBusinessName] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [cep, setCep] = useState("");
  const [phone, setPhone] = useState("");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    api.get<{ establishment_profile: EstablishmentProfile | null }>("/me").then(({ data }) => {
      const p = data.establishment_profile;
      if (p) {
        setHasProfile(true);
        setBusinessName(p.business_name || "");
        setAddressLine(p.address_line || "");
        setNeighborhood(p.neighborhood || "");
        setCity(p.city || "");
        setState(p.state || "");
        setCep(p.cep || "");
        setPhone(p.phone || "");
      }
    }).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSuccess(false);
    try {
      // Geocode address pra pegar lat/lng
      const fullAddress = [addressLine, neighborhood, city, state, cep].filter(Boolean).join(", ");
      let latitude: number | undefined;
      let longitude: number | undefined;

      if (fullAddress.length > 5) {
        const geoRes = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(fullAddress)}&format=json&limit=1&countrycodes=br`,
          { headers: { "Accept-Language": "pt-BR" } }
        );
        const geoData = await geoRes.json();
        if (geoData.length) {
          latitude = parseFloat(geoData[0].lat);
          longitude = parseFloat(geoData[0].lon);
        }
      }

      const payload = {
        business_name: businessName,
        address_line: addressLine || null,
        neighborhood: neighborhood || null,
        city: city || null,
        state: state || null,
        cep: cep || null,
        phone: phone || null,
        ...(latitude && longitude ? { latitude, longitude } : {}),
      };

      if (hasProfile) {
        await api.patch("/me/establishment-profile", payload);
      } else {
        await api.post("/me/establishment-profile", payload);
        setHasProfile(true);
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl space-y-4">
        <div className="h-8 w-48 skeleton rounded-lg" />
        <div className="h-80 skeleton rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="anim-in">
        <h2 className="text-3xl font-bold text-gray-900">Perfil do estabelecimento</h2>
        <p className="text-gray-500 mt-1">Informações visíveis pra freelancers</p>
      </div>

      <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm space-y-5 anim-in-d1">
        <div className="space-y-2">
          <Label className="text-sm font-medium">Nome do estabelecimento *</Label>
          <Input value={businessName} onChange={(e) => setBusinessName(e.target.value)} placeholder="Bar do Zé" required className="h-12 rounded-xl bg-muted border-0" />
        </div>
        <div className="space-y-2">
          <Label className="text-sm font-medium">Telefone</Label>
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="(11) 3333-4444" className="h-12 rounded-xl bg-muted border-0" />
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 ring-1 ring-black/[0.04] shadow-sm space-y-5 anim-in-d2">
        <h3 className="font-semibold text-gray-900" style={{ fontFamily: "'Instrument Serif', serif" }}>Endereço</h3>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label className="text-sm font-medium">Rua / número</Label>
            <Input value={addressLine} onChange={(e) => setAddressLine(e.target.value)} placeholder="Rua Augusta, 1234" className="h-12 rounded-xl bg-muted border-0" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Bairro</Label>
              <Input value={neighborhood} onChange={(e) => setNeighborhood(e.target.value)} placeholder="Consolação" className="h-12 rounded-xl bg-muted border-0" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">CEP</Label>
              <Input value={cep} onChange={(e) => setCep(e.target.value)} placeholder="01310-100" maxLength={8} className="h-12 rounded-xl bg-muted border-0" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Cidade</Label>
              <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="São Paulo" className="h-12 rounded-xl bg-muted border-0" />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Estado</Label>
              <Input value={state} onChange={(e) => setState(e.target.value)} placeholder="SP" maxLength={2} className="h-12 rounded-xl bg-muted border-0" />
            </div>
          </div>
        </div>
      </div>

      {success && (
        <div className="px-4 py-3 rounded-xl bg-green-50 border border-green-100">
          <p className="text-sm text-green-700">✓ Perfil salvo com sucesso!</p>
        </div>
      )}

      <Button onClick={handleSave} disabled={saving} className="rounded-full h-11 px-6">
        {saving ? "Salvando..." : "Salvar perfil"}
      </Button>
    </div>
  );
}
