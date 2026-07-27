"use client";

import { useState } from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";
import type { FreelancerSearchRead } from "@/lib/types";

interface InviteModalProps {
  freelancer: FreelancerSearchRead;
  onClose: () => void;
  onSuccess: () => void;
}

export function InviteModal({ freelancer, onClose, onSuccess }: InviteModalProps) {
  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [hourlyRate, setHourlyRate] = useState("");
  const [totalPay, setTotalPay] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!startDate || !startTime || !endTime) {
      showToast("Preencha data e horários", "error");
      return;
    }

    const startAt = new Date(`${startDate}T${startTime}:00`).toISOString();
    const endAt = new Date(`${startDate}T${endTime}:00`).toISOString();

    setSubmitting(true);
    try {
      await api.post("/invitations", {
        freelancer_id: freelancer.user_id,
        skill_category_id: "00000000-0000-0000-0000-000000000000",
        start_at: startAt,
        end_at: endAt,
        proposed_hourly_rate: hourlyRate || null,
        proposed_total_pay: totalPay || null,
        message: message || null,
      });
      onSuccess();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || "Erro ao enviar convite"
          : "Erro ao enviar convite";
      showToast(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Convidar freelancer</h3>
            <p className="text-sm text-gray-500 mt-0.5">{freelancer.display_name}</p>
          </div>
          <button type="button" onClick={onClose} className="p-2 rounded-lg hover:bg-gray-50" aria-label="Fechar">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Data do plantão *</Label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
              className="h-11 rounded-xl bg-muted border-0"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Início *</Label>
              <Input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                className="h-11 rounded-xl bg-muted border-0"
              />
            </div>
            <div className="space-y-2">
              <Label>Fim *</Label>
              <Input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
                className="h-11 rounded-xl bg-muted border-0"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Valor/hora (R$)</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={hourlyRate}
                onChange={(e) => setHourlyRate(e.target.value)}
                placeholder="30.00"
                className="h-11 rounded-xl bg-muted border-0"
              />
            </div>
            <div className="space-y-2">
              <Label>Valor total (R$)</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={totalPay}
                onChange={(e) => setTotalPay(e.target.value)}
                placeholder="200.00"
                className="h-11 rounded-xl bg-muted border-0"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Mensagem (opcional)</Label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Topa um plantão na sexta?"
              maxLength={1000}
              rows={3}
              className="rounded-xl bg-muted border-0 resize-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 rounded-full">
              Cancelar
            </Button>
            <Button type="submit" disabled={submitting} className="flex-1 rounded-full">
              {submitting ? "Enviando..." : "Enviar convite"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
