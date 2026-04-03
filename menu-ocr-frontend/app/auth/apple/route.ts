import { NextRequest, NextResponse } from "next/server";

/**
 * GET /auth/apple?redirect_to=<encoded_deep_link>
 *
 * Proxy redirect — hides the internal Supabase project URL from the address bar.
 * The browser briefly shows fooder.app/auth/apple then follows the 302.
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

  const target = `${supabaseUrl}/auth/v1/authorize?provider=apple&scopes=name%20email&redirect_to=${encodeURIComponent(
    redirectTo
  )}`;

  return NextResponse.redirect(target, { status: 302 });
}
