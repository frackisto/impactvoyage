import { forwardAuth } from "@/lib/auth/handlers";

/** POST {email, password, first_name, last_name, consent} → cookies httpOnly + {user}. */
export async function POST(request: Request) {
  return forwardAuth("auth/register/", request);
}
