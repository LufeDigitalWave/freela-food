# PWA — Progressive Web App Support

freela-food agora suporta instalação como PWA (Progressive Web App) em navegadores modernos.

## O que inclui

- **manifest.json** — Configuração de app (name, icons, theme color, shortcuts)
- **Service Worker** — Caching de assets estáticos + fallback offline
- **Meta tags** — Apple Web App, theme color, icon links
- **Offline page** — Página amigável quando conexão cai
- **Shortcuts** — Atalhos rápidos (Nova Vaga, Meus Contratos)

## Como instalar

### Android (Chrome)
1. Abra https://freela-food.com
2. Menu (⋮) → "Instalar app"
3. Confirmar

### iOS (Safari)
1. Abra https://freela-food.com em Safari
2. Compartilhar (↗️) → "Adicionar à Tela de início"
3. Confirmar

### Desktop (Chrome/Edge)
1. Abra https://freela-food.com
2. Ícone de instalação (canto da barra de endereço)
3. Confirmar

## Funcionalidades

✅ **Standalone display** — Sem barra de endereço (como app nativo)  
✅ **Offline fallback** — Página offline se conexão cair  
✅ **Caching de navegação** — Páginas públicas cached  
✅ **Atalhos rápidos** — Acessos diretos do menu inicial  
✅ **Maskable icons** — Icons adaptativos por telefone  
✅ **Theme color** — Cor laranja freela-food na barra do sistema  

## Limitações (v1)

- Service Worker desabilitado em desenvolvimento (`NODE_ENV === 'dev'`)
- Apenas páginas estáticas são pré-cachadas
- API calls não são cachadas (always network-first)
- Telas autenticadas requerem conectividade

## Ativar em desenvolvimento

```bash
# No arquivo .env.local do frontend
NEXT_PUBLIC_ENABLE_SW=true
```

Depois reinicie o dev server.

## Assets necessários (TODO)

Os ícones estão placeholder no `manifest.json`. Para deploy real:

- [ ] `/public/icon-192.png` (192x192, PNG)
- [ ] `/public/icon-512.png` (512x512, PNG)
- [ ] `/public/icon-192-maskable.png` (192x192, PNG com padding)
- [ ] `/public/icon-512-maskable.png` (512x512, PNG com padding)
- [ ] `/public/screenshot-540x720.png` (mobile screenshot)
- [ ] `/public/screenshot-1280x720.png` (desktop screenshot)

Gerar com: https://www.pwabuilder.com/ ou similar.

## Testing

Verificar em DevTools:
```
Application → Manifest — confirm all fields
Application → Service Workers — confirm registered
Application → Storage — check cache entries
```

## Referências

- MDN Web Docs: https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps
- W3C Manifest Spec: https://www.w3.org/TR/appmanifest/
- Service Worker: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
