import { forwardAuth } from "@/lib/auth/handlers";

/** POST {email, password} → cookies httpOnly + {user}. */
export async function POST(request: Request) {
  return forwardAuth("auth/login/", request);
}
