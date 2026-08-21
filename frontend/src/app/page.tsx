"use client";

import { useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useRouter } from "next/navigation";

/**
 * Root page (/).
 * Conditionally shows:
 * - Landing page if not authenticated
 * - Dashboard if authenticated
 */
export default function RootPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (user) {
        // Redirect authenticated users to dashboard
        router.push("/dashboard");
      }
      // Not authenticated: show landing below
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-gray-200 border-t-primary rounded-full animate-spin" />
          <p className="text-sm text-gray-400">Carregando...</p>
        </div>
      </div>
    );
  }

  // Render landing page for non-authenticated users
  return <LandingPage />;
}

// Landing page component (from (public)/page.tsx)
import Link from "next/link";
import { ArrowRight, Zap, Users, BarChart3, Shield } from "lucide-react";

function LandingPage() {
  return (
    <div className="overflow-hidden">
      {/* ─── Navbar ─────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-border/50">
        <nav className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <div className="flex items-center gap-2">
            <span className="text-2xl" role="img" aria-label="prato de comida">🍽️</span>
            <span className="text-xl font-bold gradient-text">freela-food</span>
          </div>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/como-funciona" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              Como funciona
            </Link>
            <Link href="/sobre" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              Sobre
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Entrar
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center justify-center h-10 px-5 rounded-full bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-all duration-200 hover:shadow-lg hover:shadow-primary/25 active:scale-[0.98]"
            >
              Cadastre-se grátis
            </Link>
          </div>
        </nav>
      </header>

      {/* ─── Hero ──────────────────────────────── */}
      <section className="relative min-h-[calc(100vh-64px)] flex items-center justify-center px-6 py-20">
        {/* Decorative elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary/5" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-primary/3" />
          <div className="absolute top-1/2 left-1/4 w-96 h-96 rounded-full bg-accent/30" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto text-center anim-in">
          <div className="mb-6">
            <span className="text-6xl md:text-7xl block mb-4" role="img" aria-label="prato de comida">🍽️</span>
          </div>
          <h1
            className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            O marketplace dos melhores profissionais de <span className="gradient-text">food service</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
            Conectamos garçons, bartenders, cozinheiros e auxiliares a bares e restaurantes que precisam de talento. Encontre oportunidades, cresça na carreira.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 anim-in-d1">
            <Link
              href="/register"
              className="inline-flex items-center justify-center gap-2 h-14 px-8 rounded-full bg-primary text-primary-foreground font-semibold text-base hover:bg-primary/90 transition-all duration-200 hover:shadow-lg hover:shadow-primary/25 active:scale-[0.98] min-w-48"
            >
              Comece agora <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/como-funciona"
              className="inline-flex items-center justify-center gap-2 h-14 px-8 rounded-full bg-secondary text-foreground font-semibold text-base hover:bg-secondary/80 transition-all duration-200 min-w-48"
            >
              Como funciona
            </Link>
          </div>

          <p className="mt-12 text-sm text-muted-foreground anim-in-d2">
            Cadastro grátis. Sem taxa de inscrição.
          </p>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── Features ───────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <h2
          className="text-4xl md:text-5xl font-bold text-center mb-16"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Por que usar freela-food?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Feature 1 */}
          <div className="card-lift p-8 rounded-2xl bg-white border border-border/50 hover:border-primary/30">
            <div className="stat-bubble bg-primary/10 mb-4">
              <Zap className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Rápido e eficiente
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Encontre oportunidades ou talentos em minutos. Sem burocracias, apenas conexões diretas.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="card-lift p-8 rounded-2xl bg-white border border-border/50 hover:border-primary/30">
            <div className="stat-bubble bg-primary/10 mb-4">
              <Users className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Comunidade verificada
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Avaliações mútuas após cada trabalho. Transparência e confiança em cada conexão.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="card-lift p-8 rounded-2xl bg-white border border-border/50 hover:border-primary/30">
            <div className="stat-bubble bg-primary/10 mb-4">
              <BarChart3 className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Histórico transparente
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Acompanhe seu histórico de trabalhos, ganhos e avaliações em um único lugar.
            </p>
          </div>

          {/* Feature 4 */}
          <div className="card-lift p-8 rounded-2xl bg-white border border-border/50 hover:border-primary/30">
            <div className="stat-bubble bg-primary/10 mb-4">
              <Shield className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Dados protegidos
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              LGPD-compliant desde o início. Seus dados são seus. Transparência garantida.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── Stats ──────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <p className="text-4xl md:text-5xl font-bold gradient-text mb-2">224</p>
            <p className="text-muted-foreground text-base">Testes backend passando</p>
          </div>
          <div className="text-center">
            <p className="text-4xl md:text-5xl font-bold gradient-text mb-2">62</p>
            <p className="text-muted-foreground text-base">Endpoints da API</p>
          </div>
          <div className="text-center">
            <p className="text-4xl md:text-5xl font-bold gradient-text mb-2">∞</p>
            <p className="text-muted-foreground text-base">Possibilidades</p>
          </div>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── CTA ────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center anim-in">
        <h2
          className="text-4xl md:text-5xl font-bold mb-6"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Pronto para começar?
        </h2>
        <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
          Junte-se a centenas de profissionais e estabelecimentos que já usam freela-food.
        </p>
        <Link
          href="/register"
          className="inline-flex items-center justify-center gap-2 h-14 px-8 rounded-full bg-primary text-primary-foreground font-semibold text-base hover:bg-primary/90 transition-all duration-200 hover:shadow-lg hover:shadow-primary/25 active:scale-[0.98] min-w-48"
        >
          Cadastre-se grátis <ArrowRight className="w-5 h-5" />
        </Link>
      </section>

      {/* ─── Footer ─────────────────────────────── */}
      <footer className="border-t border-border/50 bg-muted/30">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-1">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">🍽️</span>
                <span className="text-lg font-bold gradient-text">freela-food</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Conectando talentos da gastronomia a oportunidades. O marketplace dos melhores profissionais de food service.
              </p>
            </div>

            {/* Links — Plataforma */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
                Plataforma
              </h4>
              <ul className="space-y-2">
                <li><Link href="/como-funciona" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Como funciona</Link></li>
                <li><Link href="/register" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Cadastre-se</Link></li>
                <li><Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Entrar</Link></li>
              </ul>
            </div>

            {/* Links — Institucional */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
                Institucional
              </h4>
              <ul className="space-y-2">
                <li><Link href="/sobre" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Sobre</Link></li>
                <li><Link href="/termos" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Termos de uso</Link></li>
                <li><Link href="/privacidade" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacidade</Link></li>
              </ul>
            </div>

            {/* Contato */}
            <div>
              <h4 className="text-sm font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
                Contato
              </h4>
              <ul className="space-y-2">
                <li className="text-sm text-muted-foreground">contato@freela-food.com.br</li>
                <li>
                  <a
                    href="https://github.com/LufeDigitalWave/freela-food"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    GitHub (Open Source)
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="divider-gradient mt-8 mb-6" />

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
            <p>© {new Date().getFullYear()} freela-food. Código aberto sob licença MIT.</p>
            <div className="flex items-center gap-4">
              <Link href="/termos" className="hover:text-foreground transition-colors">Termos</Link>
              <Link href="/privacidade" className="hover:text-foreground transition-colors">Privacidade</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
