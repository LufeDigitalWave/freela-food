"use client";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <span className="text-4xl">🍽️</span>
          <h1 className="text-2xl font-bold text-gray-900 mt-3">Complete seu perfil</h1>
          <p className="text-gray-500 mt-1">Precisamos de algumas informações para você começar</p>
        </div>
        {children}
      </div>
    </div>
  );
}
