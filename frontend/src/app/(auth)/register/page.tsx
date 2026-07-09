"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, "freelancer");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao cadastrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-0 left-0 w-full h-full" style={{
          backgroundImage: `radial-gradient(circle at 75% 25%, oklch(0.65 0.18 40 / 30%) 0%, transparent 50%),
                           radial-gradient(circle at 25% 75%, oklch(0.75 0.15 55 / 20%) 0%, transparent 50%)`,
        }} />
      </div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-10 animate-fade-in-up">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center glow-amber">
              <span className="text-2xl">🍽️</span>
            </div>
            <h1 className="text-3xl font-bold gradient-text">freela-food</h1>
          </div>
          <p className="text-muted-foreground text-sm">
            Crie sua conta e encontre oportunidades
          </p>
        </div>

        <div className="glass-card rounded-2xl p-8 animate-fade-in-up-delay-1">
          <h2 className="text-xl font-semibold mb-2">Criar conta</h2>
          <p className="text-sm text-muted-foreground mb-6">Cadastro como freelancer</p>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm text-muted-foreground">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-11 bg-background/50 border-border/50 focus:border-primary/50 transition-colors"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm text-muted-foreground">Senha</Label>
              <Input
                id="password"
                type="password"
                placeholder="Mínimo 8 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="h-11 bg-background/50 border-border/50 focus:border-primary/50 transition-colors"
              />
            </div>
            {error && (
              <div className="px-3 py-2 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}
            <Button
              type="submit"
              className="w-full h-11 font-medium bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200 hover:shadow-lg hover:shadow-primary/20"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Cadastrando...
                </div>
              ) : (
                "Criar conta"
              )}
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground animate-fade-in-up-delay-2">
          Já tem conta?{" "}
          <Link href="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
            Entrar
          </Link>
        </p>
      </div>
    </div>
  );
}
