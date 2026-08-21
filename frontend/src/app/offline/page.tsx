"use client";

export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-white">
      <div className="max-w-md text-center">
        <div className="mb-6">
          <span className="text-6xl block mb-4">📱</span>
        </div>
        <h1
          className="text-3xl md:text-4xl font-bold mb-4"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Você está offline
        </h1>
        <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
          Parece que você perdeu a conexão com a internet. Verifique sua conexão e tente novamente.
        </p>
        <div className="space-y-3">
          <button
            onClick={() => window.location.reload()}
            className="w-full h-12 rounded-full bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all duration-200 active:scale-[0.98]"
          >
            Tentar novamente
          </button>
          <button
            onClick={() => window.history.back()}
            className="w-full h-12 rounded-full bg-secondary text-foreground font-semibold hover:bg-secondary/80 transition-all duration-200"
          >
            Voltar
          </button>
        </div>
      </div>
    </div>
  );
}
