/** Contrôle de santé du serveur Next.js (healthcheck Docker, Phase 24). */
export function GET() {
  return Response.json({ status: "ok", service: "voyage-site" });
}
