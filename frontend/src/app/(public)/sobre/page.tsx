import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Globe, Code2, Heart } from "lucide-react";

export const metadata: Metadata = {
  title: "Sobre | freela-food",
  description: "Conheça o freela-food: marketplace open-source bidirecional que conecta profissionais de food service a bares e restaurantes.",
};

export default function SobrePage() {
  return (
    <div className="overflow-hidden">
      {/* ─── Hero ──────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h1
          className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Sobre o freela-food
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Um marketplace open-source que nasceu da necessidade real de conectar talentos de food service a oportunidades.
        </p>
      </section>

      {/* ─── Story ──────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 pb-16">
        <div className="prose prose-lg max-w-none">
          <div className="space-y-6 text-muted-foreground leading-relaxed">
            <p className="text-base">
              O mercado de food service movimenta bilhões no Brasil. Mas encontrar o profissional certo para aquele evento do sábado,
              ou aquela substituição de última hora, ainda é feito por indicação, WhatsApp e sorte.
            </p>
            <p className="text-base">
              O <strong className="text-foreground">freela-food</strong> resolve isso com um marketplace bidirecional:
              estabelecimentos publicam vagas ou buscam profissionais diretamente; freelancers
              encontram oportunidades que combinam com suas habilidades, localização e horários.
            </p>
            <p className="text-base">
              Construído com código aberto, respeitando a LGPD desde o primeiro commit, e pensado para
              escalar do bar da esquina à rede de restaurantes.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── Values ─────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2
          className="text-3xl md:text-4xl font-bold text-center mb-12"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Nossos valores
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card-lift p-8 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Globe className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Transparência
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Código aberto, avaliações visíveis, termos claros. Sem surpresas.
            </p>
          </div>

          <div className="card-lift p-8 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Code2 className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Qualidade técnica
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              224 testes, 62 endpoints, TypeScript strict, LGPD-compliant. Engenharia séria.
            </p>
          </div>

          <div className="card-lift p-8 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Heart className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-3" style={{ fontFamily: "var(--font-sans)" }}>
              Comunidade
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Feito para profissionais reais, com regras que protegem ambos os lados.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── Open Source ─────────────────────────── */}
      <section className="max-w-4xl mx-auto px-6 py-16 text-center">
        <h2
          className="text-3xl md:text-4xl font-bold mb-6"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Open Source
        </h2>
        <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
          O freela-food é distribuído sob licença MIT. O código está no GitHub, aberto para contribuições, inspeção e aprendizado.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href="https://github.com/LufeDigitalWave/freela-food"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 h-12 px-6 rounded-full bg-foreground text-background font-semibold text-sm hover:bg-foreground/90 transition-all duration-200 active:scale-[0.98]"
          >
            <Code2 className="w-4 h-4" /> Ver no GitHub
          </a>
          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-2 h-12 px-6 rounded-full bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary/90 transition-all duration-200 hover:shadow-lg hover:shadow-primary/25 active:scale-[0.98]"
          >
            Cadastre-se <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
