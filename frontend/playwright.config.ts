import { defineConfig, devices } from "@playwright/test";

const PORT = 3100;

/**
 * Tests de bout en bout sur le build de production (`npm run build` d'abord).
 * Le backend Django doit tourner (API_URL) pour les pages qui l'interrogent.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  // Par défaut, la moitié des cœurs (12 sur la machine de développement) : trop pour un
  // seul serveur Next et le Django de développement, qui saturent et font échouer des
  // tests au hasard. 4 workers suffisent.
  workers: 4,
  reporter: [["list"]],
  // Un seul serveur de production pour tous les workers : sous charge, un changement de
  // langue (rechargement complet, autre root layout) peut dépasser les 5 s par défaut.
  expect: { timeout: 10_000 },
  use: {
    baseURL: `http://localhost:${PORT}`,
    locale: "fr-FR",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: {
    command: `npx next start -p ${PORT}`,
    url: `http://localhost:${PORT}`,
    // Jamais de réutilisation : un ancien serveur resté ouvert fausserait les tests.
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
