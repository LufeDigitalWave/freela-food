import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware — redireciona usuários autenticados de / para /dashboard.
 *
 * Não valida JWT server-side (apenas checa presença do cookie/header).
 * A validação real acontece na API (/auth/me).
 *
 * Isso permite que a landing page (/) seja server-rendered (SEO-friendly)
 * enquanto users autenticados são redirecionados imediatamente.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Só intercepta a landing page (/) para redirect autenticado
  if (pathname === "/") {
    // Verifica presença de token (cookie ou localStorage não acessível aqui)
    // Usar cookie se existir (set pelo login)
    const authCookie = request.cookies.get("access_token");
    if (authCookie?.value) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  // Só rodar nas rotas que precisam
  matcher: ["/"],
};
