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
  const [role, setRole] = useState<"freelancer" | "establishment">("freelancer");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, role);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Erro ao cadastrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side — branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center"
        style={{ background: "linear-gradient(145deg, #f59e0b 0%, #e85d2c 60%, #c2410c 100%)" }}>
        <div className="relative z-10 max-w-md text-white px-12">
          <div className="anim-in">
            <span className="text-6xl mb-6 block">{role === "freelancer" ? "👨‍🍳" : "🏪"}</span>
            <h1 className="text-4xl font-bold mb-4" style={{ fontFamily: "'Instrument Serif', serif" }}>
              {role === "freelancer"
                ? "Comece a receber convites em minutos"
                : "Encontre os melhores profissionais pra seu evento"}
            </h1>
            <p className="text-white/80 text-lg leading-relaxed">
              {role === "freelancer"
                ? "Crie seu perfil, adicione suas habilidades e raio de atuação. Estabelecimentos vão encontrar você."
                : "Publique vagas, busque freelancers por proximidade e gerencie contratos com facilidade."}
            </p>
          </div>
        </div>
        <div className="absolute -bottom-20 -right-20 w-72 h-72 rounded-full bg-white/5" />
        <div className="absolute -top-10 -left-10 w-48 h-48 rounded-full bg-white/5" />
      </div>

      {/* Right side — form */}
      <div className="flex-1 flex items-center justify-center px-6 lg:px-16 bg-white">
        <div className="w-full max-w-sm">
          <div className="mb-8 anim-in">
            <div className="flex items-center gap-2 mb-8 lg:hidden">
              <span className="text-3xl">🍽️</span>
              <span className="text-xl font-bold gradient-text">freela-food</span>
            </div>
            <h2 className="text-3xl font-bold text-foreground">Criar conta</h2>
            <p className="text-muted-foreground mt-2">Cadastro grátis na plataforma</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 anim-in-d1">
            {/* Role selector */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Eu sou</Label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRole("freelancer")}
                  className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 ${
                    role === "freelancer"
                      ? "border-primary bg-orange-50 shadow-sm"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <span className="text-2xl">👨‍🍳</span>
                  <span className={`text-sm font-medium ${
                    role === "freelancer" ? "text-primary" : "text-gray-600"
                  }`}>Freelancer</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRole("establishment")}
                  className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200 ${
                    role === "establishment"
                      ? "border-primary bg-orange-50 shadow-sm"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <span className="text-2xl">🏪</span>
                  <span className={`text-sm font-medium ${
                    role === "establishment" ? "text-primary" : "text-gray-600"
                  }`}>Estabelecimento</span>
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">Email</Label>
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
              <Label htmlFor="password" className="text-sm font-medium">Senha</Label>
              <Input
                id="password"
                type="password"
                placeholder="Mínimo 8 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
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
                  Cadastrando...
                </div>
              ) : (
                "Criar minha conta"
              )}
            </Button>
          </form>

          <p className="mt-8 text-center text-sm text-muted-foreground anim-in-d2">
            Já tem conta?{" "}
            <Link href="/login" className="text-primary hover:text-primary/80 font-semibold transition-colors">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
