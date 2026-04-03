import { NextRequest, NextResponse } from "next/server";

/**
 * GET /auth/google?redirect_to=<encoded_deep_link>
 *
 * Proxy redirect — hides the internal Supabase project URL from the address bar.
 * The browser briefly shows fooder.app/auth/google then follows the 302 to the
 * real Google OAuth endpoint.
 */
export async function GET(request: NextRequest) {
  const redirectTo =
    request.nextUrl.searchParams.get("redirect_to") ?? "";

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!supabaseUrl) {
    return NextResponse.json(
      { error: "Server misconfiguration" },
      { status: 500 }
    );
  }

  const target = `${supabaseUrl}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(
    redirectTo
  )}`;

  return NextResponse.redirect(target, { status: 302 });
}
