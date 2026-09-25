# Frontend — Impact Voyage et Logistique

Next.js 16 (App Router, Turbopack) · TypeScript strict · Tailwind CSS 4 · shadcn/ui ·
next-intl (FR/EN) · TanStack Query · React Hook Form + Zod · Axios.

> Next.js 16 diffère des versions précédentes (ex. `middleware.ts` → `proxy.ts`,
> `params` / `cookies()` asynchrones). La documentation de la version installée est
> dans `node_modules/next/dist/docs/` (voir `AGENTS.md`).

## Démarrage

```bash
cp .env.example .env.local   # API_URL=http://localhost:8000/api/v1
npm install
npm run dev                  # http://localhost:3000 (le backend Django doit tourner)
```

| Script | Rôle |
|---|---|
| `npm run dev` / `build` / `start` | Développement, build de production, serveur de production |
| `npm run lint` · `npm run typecheck` · `npm test` | ESLint, TypeScript, Vitest |
| `npm run api:types` | Régénère `types/api.d.ts` depuis le schéma OpenAPI du backend |

## Architecture

```
app/
├── [locale]/            # pages, dans la langue de l'URL (fr sans préfixe, /en/...)
├── api/auth/            # BFF : connexion, inscription, déconnexion, session (cookies httpOnly)
├── api/backend/[...path]# BFF : relais authentifié vers l'API Django
├── fonts.ts             # Fredoka (titres), Nunito (texte), Dancing Script (slogan)
└── globals.css          # charte : couleurs du logo et rôles shadcn/ui
proxy.ts                 # langue (next-intl) + pages privées (/profile) et rafraîchissement du jeton
i18n/  messages/         # routage des langues, textes FR/EN
lib/api/                 # backend.ts (serveur → Django), server.ts (apiGet), client.ts (Axios)
lib/auth/                # cookies, lecture d'expiration JWT, relais d'authentification
types/                   # api.d.ts généré + raccourcis (types/index.ts)
```

**Authentification** : le navigateur n'a jamais accès aux jetons JWT. Les Route Handlers
`/api/auth/*` les reçoivent de Django et les posent en cookies `httpOnly` ; les Client
Components appellent l'API via `/api/backend/*`, qui ajoute le jeton et le rafraîchit au
besoin. Les Server Components utilisent `apiGet()` (langue et devise du visiteur, cache ISR).

**Appels depuis un Client Component** : `api.get("tours", { params: { travelers: 2 } })`
— chemins sans barre finale ; les erreurs sont des `ApiError` (`code`, `message`,
`fieldErrors()` pour les formulaires).

## Charte graphique

Couleurs extraites du logo, déclinées en nuances OKLCH (`ocean-50` … `ocean-950`,
`sunset-50` … `sunset-950`) :

| Rôle | Couleur | Usage |
|---|---|---|
| `primary` | `ocean-600` (bleu du logo, nuance accessible) | Boutons principaux, liens, texte blanc |
| `cta` | `sunset-500` = `#F89832` (orange du logo) | « Demander un devis », texte `ocean-950` |
| `foreground` | `ocean-950` | Texte courant (bleu nuit) |

Contraste WCAG AA : jamais de texte blanc sur l'orange (2,2:1) ni sur `ocean-500` (3,6:1).
