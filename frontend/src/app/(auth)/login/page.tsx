"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao fazer login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side — branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center"
        style={{ background: "linear-gradient(145deg, #e85d2c 0%, #dc4a1a 50%, #c2410c 100%)" }}>
        <div className="relative z-10 max-w-md text-white px-12">
          <div className="anim-in">
            <span className="text-6xl mb-6 block">🍽️</span>
            <h1 className="text-4xl font-bold mb-4" style={{ fontFamily: "'Instrument Serif', serif" }}>
              O marketplace dos melhores profissionais de food service
            </h1>
            <p className="text-white/80 text-lg leading-relaxed">
              Garçons, bartenders, cozinheiros e auxiliares conectados a bares e restaurantes que precisam de talento.
            </p>
          </div>
        </div>
        {/* Decorative circles */}
        <div className="absolute -bottom-20 -left-20 w-72 h-72 rounded-full bg-white/5" />
        <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-white/5" />
        <div className="absolute top-1/3 right-10 w-24 h-24 rounded-full bg-white/10" />
      </div>

      {/* Right side — form */}
      <div className="flex-1 flex items-center justify-center px-6 lg:px-16 bg-white">
        <div className="w-full max-w-sm">
          <div className="mb-8 anim-in">
            <div className="flex items-center gap-2 mb-8 lg:hidden">
              <span className="text-3xl">🍽️</span>
              <span className="text-xl font-bold gradient-text">freela-food</span>
            </div>
            <h2 className="text-3xl font-bold text-foreground">Bem-vindo de volta</h2>
            <p className="text-muted-foreground mt-2">Entre na sua conta pra continuar</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 anim-in-d1">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-foreground">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-12 rounded-xl bg-muted border-0 focus:ring-2 focus:ring-primary/20 text-base"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium text-foreground">Senha</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-12 rounded-xl bg-muted border-0 focus:ring-2 focus:ring-primary/20 text-base"
              />
            </div>
            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}
            <Button
              type="submit"
              className="w-full h-12 rounded-full font-semibold text-base bg-primary hover:bg-primary/90 transition-all duration-200 active:scale-[0.98] hover:shadow-lg hover:shadow-primary/25"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Entrando...
                </div>
              ) : (
                "Entrar"
              )}
            </Button>
          </form>

          <p className="mt-8 text-center text-sm text-muted-foreground anim-in-d2">
            Não tem conta?{" "}
            <Link href="/register" className="text-primary hover:text-primary/80 font-semibold transition-colors">
              Cadastre-se grátis
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
