"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { FreelancerProfile } from "@/lib/types";

export default function ProfilePage() {
  const [profile, setProfile] = useState<FreelancerProfile | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [phone, setPhone] = useState("");
  const [pixKey, setPixKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

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
    });
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
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <h2 className="text-2xl font-bold">Meu perfil</h2>

      <Card>
        <CardHeader>
          <CardTitle>Dados pessoais</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Nome de exibição</Label>
            <Input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Como você quer ser chamado"
            />
          </div>
          <div className="space-y-2">
            <Label>Bio</Label>
            <Textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Conte sobre sua experiência..."
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Telefone</Label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="(11) 99999-9999"
            />
          </div>
          <div className="space-y-2">
            <Label>Chave Pix</Label>
            <Input
              value={pixKey}
              onChange={(e) => setPixKey(e.target.value)}
              placeholder="CPF, email, telefone ou chave aleatória"
            />
          </div>

          {success && (
            <p className="text-sm text-green-600">✓ Perfil salvo com sucesso!</p>
          )}

          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Salvando..." : "Salvar"}
          </Button>
        </CardContent>
      </Card>

      {/* Stats */}
      {profile && (
        <Card>
          <CardHeader>
            <CardTitle>Estatísticas</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold">{profile.completed_contracts_count}</p>
                <p className="text-xs text-muted-foreground">Contratos</p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {profile.average_rating ? profile.average_rating.toFixed(1) : "—"}
                </p>
                <p className="text-xs text-muted-foreground">Rating</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{profile.total_reviews}</p>
                <p className="text-xs text-muted-foreground">Reviews</p>
              </div>
              <div>
                <p className="text-2xl font-bold">{profile.no_show_count}</p>
                <p className="text-xs text-muted-foreground">No-shows</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
