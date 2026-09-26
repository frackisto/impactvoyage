# Frontend — Impact Voyage et Logistique

Next.js 16 (App Router, Turbopack) · TypeScript strict · Tailwind CSS 4 · shadcn/ui ·
next-intl (FR/EN) · TanStack Query · React Hook Form + Zod · Axios.

> Next.js 16 diffère des versions précédentes (ex. `middleware.ts` → `proxy.ts`,
> `params` / `cookies()` asynchrones). La documentation de la version installée est
> dans `node_modules/next/dist/docs/` (voir `AGENTS.md`).

## Démarrage

```bash
cp .env.example .env.local   # API_URL=http://localhost:8000/api/v1
# + FRONTEND_SHARED_SECRET : même valeur que dans le .env racine (limitation de débit)
npm install
npm run dev                  # http://localhost:3000 (le backend Django doit tourner)
```

| Script | Rôle |
|---|---|
| `npm run dev` / `build` / `start` | Développement, build de production, serveur de production |
| `npm run lint` · `npm run typecheck` · `npm test` | ESLint, TypeScript, Vitest |
| `npm run test:e2e` | Playwright (bureau + mobile, 4 workers, cache de données vidé au démarrage) et audit d'accessibilité axe — après `npm run build` ; suppose `load_agency_content` et `seed_demo` |
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

## Design system

- `components/ui/` : composants shadcn/ui adaptés à la charte (boutons de 40/44 px pour le
  tactile, variantes `cta` et `inverse`, badges d'offre, libellés traduits).
- `components/common/` : briques du site — `ContentCard` (carte cliquable avec effet au
  survol), `Price` (devise choisie, conversion indicative), `Rating`, `OfferBadge`,
  `SectionHeading`, `PageHeader` (fil d'Ariane), `EmptyState`, `ErrorState`, squelettes.
- `components/layout/` : en-tête collant (barre de contact, menu, « Plus », recherche,
  devis), menu mobile, sélecteurs de langue et de devise, pied de page (coordonnées issues
  des paramètres du site).
- Page de référence : **`/charte-graphique`** (non indexée) — palette, typographies,
  composants, formulaire modèle (React Hook Form + Zod), états.
- Autres briques partagées : `Section`/`SectionHeader` (sections de page), `Breadcrumbs`,
  `Pagination` (liens, logique dans `lib/pagination.ts`), `Gallery` (visionneuse au
  clavier), `ReviewList`, `JsonLd` et `lib/seo.ts` (URL canonique, hreflang),
  `ImmersiveHero` (en-tête des fiches), `FilterPanel` / `SortSelect` / `CatalogLayout`
  (listes filtrables décrites par une configuration de champs), `SegmentedNav`,
  `lib/stay.ts` (séjour lu dans l'URL, nuits), `lib/search-params.ts` (lecture tolérante des
  filtres d'URL), `lib/text.ts` (paragraphes, résumés).
- Traductions : `messages/messages.test.ts` vérifie la syntaxe ICU de chaque message et
  l'égalité des clés FR/EN. Attention : en ICU, une apostrophe devant `#`, `{` ou `}` ouvre
  une citation (« d'# » est invalide ; écrire « d'un »).

## Crédits

Drapeaux sous Windows : police « Twemoji Country Flags »
([country-flag-emoji-polyfill](https://github.com/talkjs/country-flag-emoji-polyfill), MIT),
graphismes [Twemoji](https://github.com/twitter/twemoji) © Twitter, sous licence
[CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Charte graphique

Couleurs extraites du logo, déclinées en nuances OKLCH (`ocean-50` … `ocean-950`,
`sunset-50` … `sunset-950`) :

| Rôle | Couleur | Usage |
|---|---|---|
| `primary` | `ocean-600` (bleu du logo, nuance accessible) | Boutons principaux, liens, texte blanc |
| `cta` | `sunset-500` = `#F89832` (orange du logo) | « Demander un devis », texte `ocean-950` |
| `foreground` | `ocean-950` | Texte courant (bleu nuit) |

Contraste WCAG AA : jamais de texte blanc sur l'orange (2,2:1) ni sur `ocean-500` (3,6:1).
