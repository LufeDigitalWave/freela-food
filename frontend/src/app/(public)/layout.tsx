import Link from "next/link";

/**
 * Layout público para páginas de marketing (como-funciona, sobre, termos, privacidade, etc.)
 * Reutiliza navbar e footer do design da landing.
 */
export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen">
      {/* ─── Navbar ─────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-border/50">
        <nav className="max-w-6xl mx-auto flex items-center justify-between px-6 h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl" role="img" aria-label="prato de comida">🍽️</span>
            <span className="text-xl font-bold gradient-text">freela-food</span>
          </Link>

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

      {/* ─── Content ────────────────────────────── */}
      <main className="flex-1">{children}</main>

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

