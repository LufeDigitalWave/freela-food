import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Briefcase, Search, HandshakeIcon, Star, Bell, Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Como funciona | freela-food",
  description: "Entenda como funciona o freela-food: publique vagas, encontre talentos, faça convites diretos e cresça na carreira de food service.",
};

export default function ComoFuncionaPage() {
  return (
    <div className="overflow-hidden">
      {/* ─── Hero ──────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h1
          className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Como funciona
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Dois caminhos, um objetivo: conectar os melhores profissionais de food service às melhores oportunidades.
        </p>
      </section>

      {/* ─── Fluxo A ────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="mb-12 text-center">
          <span className="inline-block px-4 py-1 rounded-full bg-primary/10 text-primary text-sm font-semibold mb-4">
            Fluxo A
          </span>
          <h2
            className="text-3xl md:text-4xl font-bold mb-4"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            Vagas públicas
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            O estabelecimento publica e os freelancers se candidatam.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Briefcase className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              1. Publicar vaga
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Estabelecimento cria uma vaga com data, horário, cargo e valor oferecido.
            </p>
          </div>

          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Search className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              2. Candidatar-se
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Freelancers compatíveis são notificados e se candidatam à vaga.
            </p>
          </div>

          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <HandshakeIcon className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              3. Contrato firmado
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Ao aceitar um candidato, o contrato é criado automaticamente. Simples assim.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── Fluxo B ────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="mb-12 text-center">
          <span className="inline-block px-4 py-1 rounded-full bg-accent text-accent-foreground text-sm font-semibold mb-4">
            Fluxo B
          </span>
          <h2
            className="text-3xl md:text-4xl font-bold mb-4"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            Convites diretos
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Encontre o profissional perfeito e faça um convite personalizado.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-accent mx-auto mb-4">
              <Search className="w-6 h-6 text-accent-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              1. Buscar freelancers
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Filtre por habilidade, proximidade, disponibilidade e avaliação.
            </p>
          </div>

          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-accent mx-auto mb-4">
              <Bell className="w-6 h-6 text-accent-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              2. Enviar convite
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Proponha termos: datas, valor, mensagem personalizada. O freelancer decide.
            </p>
          </div>

          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-accent mx-auto mb-4">
              <HandshakeIcon className="w-6 h-6 text-accent-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              3. Contrato direto
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Aceito o convite, o contrato é gerado diretamente. Sem etapas extras.
            </p>
          </div>
        </div>
      </section>

      {/* ─── Divider ────────────────────────────── */}
      <div className="max-w-6xl mx-auto px-6">
        <div className="divider-gradient" />
      </div>

      {/* ─── After ──────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="mb-12 text-center">
          <h2
            className="text-3xl md:text-4xl font-bold mb-4"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            Depois do trabalho
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Avaliações mútuas constroem reputação e confiança na plataforma.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Star className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              Avaliação mútua
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Freelancer e estabelecimento avaliam um ao outro após cada serviço.
            </p>
          </div>

          <div className="card-lift p-6 rounded-2xl border border-border/50 text-center">
            <div className="stat-bubble bg-primary/10 mx-auto mb-4">
              <Shield className="w-6 h-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground mb-2" style={{ fontFamily: "var(--font-sans)" }}>
              Anti-retaliação
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Avaliações ficam ocultas até ambos avaliarem (ou 7 dias). Transparência sem medo.
            </p>
          </div>
        </div>
      </section>

      {/* ─── CTA ────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h2
          className="text-3xl md:text-4xl font-bold mb-6"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Pronto para participar?
        </h2>
        <Link
          href="/register"
          className="inline-flex items-center justify-center gap-2 h-14 px-8 rounded-full bg-primary text-primary-foreground font-semibold text-base hover:bg-primary/90 transition-all duration-200 hover:shadow-lg hover:shadow-primary/25 active:scale-[0.98] min-w-48"
        >
          Crie sua conta <ArrowRight className="w-5 h-5" />
        </Link>
      </section>
    </div>
  );
}
