import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  // ?next= is set by /auth/login when redirecting through OAuth
  const next = requestUrl.searchParams.get("next") ?? "/";

  if (code) {
    const supabase = createClient(supabaseUrl, supabaseKey);
    await supabase.auth.exchangeCodeForSession(code);
  }

  // Redirect to the original destination, falling back to home
  return NextResponse.redirect(new URL(next, requestUrl.origin));
}

