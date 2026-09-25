import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/api/backend";
import { clearAuthCookies, REFRESH_COOKIE } from "@/lib/auth/cookies";

/** Révoque le refresh token côté Django puis efface les cookies. */
export async function POST() {
  const refresh = (await cookies()).get(REFRESH_COOKIE)?.value;
  if (refresh) {
    await backendFetch("auth/logout/", {
      method: "POST",
      json: { refresh },
      cache: "no-store",
    }).catch(() => null); // la déconnexion locale a lieu même si Django est injoignable
  }
  const response = new NextResponse(null, { status: 204 });
  clearAuthCookies(response.cookies);
  return response;
}
