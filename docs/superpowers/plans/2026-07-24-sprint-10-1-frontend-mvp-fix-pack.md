# Sprint 10.1 — Frontend MVP Fix Pack Implementation Plan

> **For agentic workers:** Use `/tdd-orchestrator` or execute task-by-task. TDD: tests first, then implementation.

**Goal:** Corrigir lacunas críticas do frontend (mobile nav, candidaturas/candidatos reais, UX consistente, responsividade). Transformar demo avançada em MVP navegável.

**Spec:** `docs/superpowers/specs/2026-07-24-sprint-10-1-frontend-mvp-fix-pack-design.md`

**Tech Stack:** Next.js 16, React 19, TypeScript strict, Tailwind v4, shadcn/ui, Axios, react-hook-form + zod.

**Test DB:** Reutilizar mesma VPS (porta 5435). Ou rodar sem backend se precisar (mock data).

---

## Task 1: Setup + Mobile Nav Component

**Files:**
- Create: `frontend/src/components/layout/bottom-tabs.tsx`
- Create: `frontend/src/components/layout/mobile-drawer.tsx`
- Modify: `frontend/src/components/layout/header.tsx`

**Steps:**

- [ ] **Step 1: Criar componente `BottomTabs`**

Criar `frontend/src/components/layout/bottom-tabs.tsx`:

```tsx
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Home, ShoppingBag, FileText, Bell, User } from 'lucide-react';

interface TabItem {
  icon: React.ReactNode;
  label: string;
  href: string;
  isActive: boolean;
}

interface BottomTabsProps {
  role: 'freelancer' | 'establishment';
}

export function BottomTabs({ role }: BottomTabsProps) {
  const pathname = usePathname();

  const freelancerTabs: TabItem[] = [
    { icon: <Home size={24} />, label: 'Início', href: '/', isActive: pathname === '/' },
    { icon: <ShoppingBag size={24} />, label: 'Vagas', href: '/jobs', isActive: pathname.startsWith('/jobs') },
    { icon: <FileText size={24} />, label: 'Contratos', href: '/contracts', isActive: pathname.startsWith('/contracts') },
    { icon: <Bell size={24} />, label: 'Notif', href: '/notifications', isActive: pathname === '/notifications' },
    { icon: <User size={24} />, label: 'Perfil', href: '/profile', isActive: pathname === '/profile' },
  ];

  const establishmentTabs: TabItem[] = [
    { icon: <Home size={24} />, label: 'Início', href: '/', isActive: pathname === '/' },
    { icon: <ShoppingBag size={24} />, label: 'Vagas', href: '/jobs/mine', isActive: pathname.startsWith('/jobs') },
    { icon: <FileText size={24} />, label: 'Candidatos', href: '/candidates', isActive: pathname === '/candidates' },
    { icon: <Bell size={24} />, label: 'Notif', href: '/notifications', isActive: pathname === '/notifications' },
    { icon: <User size={24} />, label: 'Perfil', href: '/profile', isActive: pathname === '/profile' },
  ];

  const tabs = role === 'freelancer' ? freelancerTabs : establishmentTabs;

  return (
    <div className="fixed bottom-0 left-0 right-0 md:hidden border-t bg-white flex justify-around">
      {tabs.map((tab) => (
        <Link key={tab.href} href={tab.href} className={`flex-1 py-3 flex flex-col items-center gap-1 text-xs ${
          tab.isActive ? 'text-primary border-b-2 border-primary' : 'text-gray-600'
        }`}>
          {tab.icon}
          {tab.label}
        </Link>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Criar componente `MobileDrawer`**

Criar `frontend/src/components/layout/mobile-drawer.tsx`:

```tsx
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Menu } from 'lucide-react';
import Link from 'next/link';

export function MobileDrawer() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button className="md:hidden" aria-label="Menu">
          <Menu size={24} />
        </button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64">
        <nav className="flex flex-col gap-4 mt-8">
          <Link href="/" className="text-lg font-medium hover:underline">Início</Link>
          <Link href="/profile" className="text-lg font-medium hover:underline">Perfil</Link>
          <Link href="/reviews" className="text-lg font-medium hover:underline">Avaliações</Link>
          <Link href="/payments" className="text-lg font-medium hover:underline">Pagamentos</Link>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
```

- [ ] **Step 3: Atualizar `header.tsx` com hamburger**

Modificar `frontend/src/components/layout/header.tsx` para adicionar drawer trigger:

```tsx
import { MobileDrawer } from './mobile-drawer';

// dentro do header component, adicionar:
<div className="md:hidden flex items-center gap-4">
  <MobileDrawer />
  {/* bell icon existente */}
</div>
```

- [ ] **Step 4: Atualizar `layout.tsx` do dashboard**

Modificar `frontend/src/app/(dashboard)/layout.tsx`:

```tsx
import { BottomTabs } from '@/components/layout/bottom-tabs';

// dentro do layout, após main content:
<BottomTabs role={user?.role as 'freelancer' | 'establishment'} />
```

- [ ] **Step 5: Esconder sidebar em mobile**

Modificar `frontend/src/components/layout/sidebar.tsx`:

Trocar `hidden md:flex` por `hidden lg:flex` (ou manter `md:flex` mas aplicar `pb-20` no main content em mobile pra não cobrir bottom tabs).

- [ ] **Step 6: Validar TypeScript**

Run: `npm run lint`

Expected: sem erros.

---

## Task 2: Corrigir `/applications` — Candidaturas Reais

**Files:**
- Modify: `frontend/src/app/(dashboard)/applications/page.tsx`
- Modify: `frontend/src/lib/api.ts` (se precisar novo tipo)
- Modify: `frontend/src/lib/types.ts` (se não tiver tipo Application)

**Steps:**

- [ ] **Step 1: Verificar tipo `Application` em types.ts**

Read: `frontend/src/lib/types.ts`

Se não existir, adicionar:

```tsx
export interface Application {
  id: string;
  job_posting_id: string;
  freelancer_id: string;
  status: 'pending' | 'accepted' | 'rejected' | 'withdrawn';
  message: string | null;
  created_at: string;
}
```

- [ ] **Step 2: Verificar endpoint `/me/applications` no backend**

Check: backend `app/api/v1/applications/router.py` — existe `GET /applications` ou `/me/applications`?

Se não existir, usar fallback: `GET /me/contracts` com filtro status.

- [ ] **Step 3: Reescrever `applications/page.tsx`**

Reescrever para chamar endpoint correto e exibir candidaturas reais:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Application } from '@/lib/types';

export default function ApplicationsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        // Tentar endpoint real; fallback se não existir
        const response = await api.get('/me/applications');
        setApps(response.data.items || response.data);
      } catch (error) {
        console.error('Error fetching applications:', error);
        // Fallback: buscar contratos (não candidaturas, mas melhor que nada)
      } finally {
        setLoading(false);
      }
    };
    fetchApplications();
  }, []);

  if (loading) return <div>Carregando...</div>;
  if (apps.length === 0) return <div>Nenhuma candidatura.</div>;

  return (
    <div className="space-y-4">
      {apps.map((app) => (
        <div key={app.id} className="p-4 border rounded-lg">
          <h3>Vaga {app.job_posting_id}</h3>
          <p>Status: {app.status}</p>
          {app.message && <p>{app.message}</p>}
          {app.status === 'pending' && (
            <button onClick={() => handleWithdraw(app.id)} className="btn-sm">
              Retirar candidatura
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Implementar `handleWithdraw`**

Adicionar função:

```tsx
const handleWithdraw = async (appId: string) => {
  try {
    await api.post(`/applications/${appId}/withdraw`);
    setApps(apps.filter(a => a.id !== appId));
    showToast('Candidatura retirada', 'success');
  } catch (error) {
    showToast('Erro ao retirar candidatura', 'error');
  }
};
```

- [ ] **Step 5: Validar TypeScript**

Run: `npm run lint`

---

## Task 3: Corrigir `/candidates` — Candidatos por Vaga

**Files:**
- Modify: `frontend/src/app/(dashboard)/candidates/page.tsx`

**Steps:**

- [ ] **Step 1: Reescrever `candidates/page.tsx`**

Reescrever para iterar vagas e buscar candidatos por vaga:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { JobPosting, Application } from '@/lib/types';

interface JobWithApplications {
  job: JobPosting;
  applications: Application[];
}

export default function CandidatesPage() {
  const [jobsWithApps, setJobsWithApps] = useState<JobWithApplications[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobsAndCandidates = async () => {
      try {
        // 1. Buscar vagas do establishment
        const jobsRes = await api.get('/jobs'); // ou /jobs/mine
        const jobs = jobsRes.data.items || jobsRes.data;

        // 2. Para cada vaga, buscar candidaturas
        const results = await Promise.all(
          jobs.map(async (job: JobPosting) => {
            try {
              const appsRes = await api.get(`/jobs/${job.id}/applications`);
              return {
                job,
                applications: appsRes.data.items || appsRes.data || [],
              };
            } catch {
              return { job, applications: [] };
            }
          })
        );

        setJobsWithApps(results);
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchJobsAndCandidates();
  }, []);

  if (loading) return <div>Carregando...</div>;
  if (jobsWithApps.length === 0) return <div>Nenhuma vaga.</div>;

  return (
    <div className="space-y-6">
      {jobsWithApps.map(({ job, applications }) => (
        <div key={job.id} className="border rounded-lg p-4">
          <h3 className="text-lg font-bold">{job.title || `Vaga ${job.skill_category_id}`}</h3>
          <p className="text-sm text-gray-600">{applications.length} candidatos</p>
          <div className="space-y-2 mt-3">
            {applications.length === 0 ? (
              <p className="text-gray-500">Nenhum candidato ainda.</p>
            ) : (
              applications.map((app) => (
                <div key={app.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div>
                    <p>Freelancer: {app.freelancer_id}</p>
                    <p className="text-sm text-gray-600">Status: {app.status}</p>
                  </div>
                  {app.status === 'pending' && (
                    <div className="flex gap-2">
                      <button onClick={() => handleAccept(app.id)} className="btn-sm btn-primary">
                        Aceitar
                      </button>
                      <button onClick={() => handleReject(app.id)} className="btn-sm btn-outline">
                        Rejeitar
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Implementar handlers**

Adicionar funções de aceitar/rejeitar:

```tsx
const handleAccept = async (appId: string) => {
  try {
    await api.post(`/applications/${appId}/accept`);
    // Refetch ou atualizar state
    showToast('Candidato aceito', 'success');
  } catch (error) {
    showToast('Erro ao aceitar candidato', 'error');
  }
};

const handleReject = async (appId: string) => {
  try {
    await api.post(`/applications/${appId}/reject`);
    // Refetch ou atualizar state
    showToast('Candidato rejeitado', 'success');
  } catch (error) {
    showToast('Erro ao rejeitar candidato', 'error');
  }
};
```

- [ ] **Step 3: Validar TypeScript**

---

## Task 4: UX Consistente — Alerts → Toast + Responsividade

**Files:**
- Modify: `frontend/src/app/(dashboard)/jobs/page.tsx`
- Modify: `frontend/src/app/(dashboard)/jobs/new/page.tsx`
- Modify: `frontend/src/app/(dashboard)/profile/page.tsx`

**Steps:**

- [ ] **Step 1: Trocar `alert()` em `jobs/page.tsx`**

Read: `frontend/src/app/(dashboard)/jobs/page.tsx`

Encontrar linhas com `alert()` (aprox. linhas 35, 57) e trocar por `showToast()` ou usar componente toast existente.

Exemplo:
```tsx
// Antes:
alert('Vaga criada com sucesso!');

// Depois:
import { showToast } from '@/components/ui/toast'; // ou relevante
showToast('Vaga criada com sucesso!', 'success');
```

- [ ] **Step 2: Ajustar grids em `jobs/new/page.tsx`**

Read: `frontend/src/app/(dashboard)/jobs/new/page.tsx`

Encontrar `grid-cols-3` (aprox. linha 121) e trocar por:
```tsx
className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4"
```

- [ ] **Step 3: Ajustar grids em `profile/page.tsx`**

Read: `frontend/src/app/(dashboard)/profile/page.tsx`

Encontrar `grid-cols-2` (aprox. linhas 129, 266, 276) e trocar por:
```tsx
className="grid grid-cols-1 sm:grid-cols-2 gap-4"
```

- [ ] **Step 4: Validar TypeScript**

---

## Task 5: Criar `frontend/.env.example`

**Files:**
- Create: `frontend/.env.example`

**Steps:**

- [ ] **Step 1: Criar `.env.example`**

Create file with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/v1
```

- [ ] **Step 2: Documentar em README**

Read: `frontend/README.md`

Adicionar seção (ou atualizar seção existente) explicando `.env.local`:

```markdown
## Setup

Copy `.env.example` to `.env.local` and configure:

```bash
cp .env.example .env.local
# Edit NEXT_PUBLIC_API_URL if backend is on different host/port
```
```

---

## Task 6: Validação Final + Build

**Steps:**

- [ ] **Step 1: Instalar dependencies**

Run: `cd frontend && npm install`

Expected: `node_modules/` criado, sem erros.

- [ ] **Step 2: Lint**

Run: `npm run lint`

Expected: sem erros (ou apenas warnings de style que aceitamos).

- [ ] **Step 3: Build**

Run: `npm run build`

Expected: build sucesso, `.next/` criado.

- [ ] **Step 4: TypeScript check**

Run: `npx tsc --noEmit`

Expected: sem erros de tipo.

- [ ] **Step 5: Commit**

Run:
```bash
git add .
git commit -m "feat(sprint-10.1): frontend fix pack - mobile nav + candidaturas reais + responsividade

- Add bottom tabs + drawer for mobile navigation
- Fix /applications to show real candidaturas
- Fix /candidates to list applicants grouped by job
- Replace alert() with showToast() for UX consistency
- Fix grids responsiveness (grid-cols-3 -> grid-cols-1 sm:grid-cols-3)
- Add frontend/.env.example
- npm run lint + npm run build passing

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Push**

Run: `git push origin main`

---

## Acceptance Criteria

- [ ] Mobile nav works on devices < md breakpoint (mobile/tablet)
- [ ] Freelancer sees real candidaturas in `/applications`
- [ ] Establishment sees candidatos grouped by vaga in `/candidates`
- [ ] All alerts replaced with toast (consistent UX)
- [ ] Grids are responsive (mobile-first)
- [ ] `.env.example` exists and is documented
- [ ] `npm run lint` passes
- [ ] `npm run build` passes
- [ ] TypeScript strict mode passes
- [ ] All changes committed and pushed

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `/me/applications` endpoint doesn't exist | Fallback: usar `/me/contracts` ou criar mock data |
| `/jobs/{id}/applications` endpoint doesn't exist | Fallback: mock data de candidatos |
| Sheet component (drawer) não existe em shadcn/ui | Usar componente customizado ou Dialog como fallback |
| Mobile nav layout quebra em alguns breakpoints | Testar em various device sizes (DevTools) |

---

## Next Steps

Após Sprint 10.1 completa:
1. Sprint 10.2: Fluxo B frontend (busca + convites)
2. Sprint 10.3: Onboarding pós-cadastro
3. Sprint 11: Deploy MVP VPS
