#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# Update Supabase Auth email templates to "Fooder" branding
#
# Prerequisites:
#   1. Go to https://supabase.com/dashboard/account/tokens
#   2. Create a personal access token
#   3. Run: SUPABASE_ACCESS_TOKEN=<your-token> bash scripts/update_supabase_email_templates.sh
# ──────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_REF="jlfqzcaospvspmzbvbxd"
API="https://api.supabase.com/v1/projects/${PROJECT_REF}/config/auth"

if [[ -z "${SUPABASE_ACCESS_TOKEN:-}" ]]; then
  echo "ERROR: Set SUPABASE_ACCESS_TOKEN first."
  echo "  Get one at: https://supabase.com/dashboard/account/tokens"
  exit 1
fi

echo "→ Updating Fooder auth email templates for project ${PROJECT_REF}..."

# Fooder brand colors
VIOLET="#7C3AED"
RED="#E53E3E"
WHITE="#FFFFFF"
LIGHT_BG="#F5F0FF"

# Common HTML wrapper
read -r -d '' HEADER <<'EOHTML' || true
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background:#F5F0FF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F0FF;padding:40px 0">
<tr><td align="center">
<table width="480" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(124,58,237,0.08)">
<tr><td style="background:#7C3AED;padding:32px 24px;text-align:center">
  <span style="font-size:32px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px">F<span style="color:#E53E3E">o</span>oder</span>
  <br><span style="font-size:13px;color:rgba(255,255,255,0.8);letter-spacing:0.5px">Scan menus. Eat smarter.</span>
</td></tr>
<tr><td style="padding:32px 28px">
EOHTML

read -r -d '' FOOTER <<'EOHTML' || true
</td></tr>
<tr><td style="padding:16px 28px 24px;text-align:center;border-top:1px solid #EDE9FE">
  <span style="font-size:12px;color:#9CA3AF">© 2026 Fooder. All rights reserved.</span>
</td></tr>
</table>
</td></tr></table>
</body></html>
EOHTML

BUTTON_STYLE="display:inline-block;background:#7C3AED;color:#FFFFFF;font-weight:700;font-size:16px;padding:14px 32px;border-radius:12px;text-decoration:none"

# ── Confirmation (signup) ────────────────────────────────────
CONFIRM_SUBJECT="Welcome to Fooder — Confirm your email"
CONFIRM_BODY="${HEADER}
<h2 style=\"margin:0 0 12px;font-size:22px;color:#1E1E1E\">Welcome to Fooder! 🍅</h2>
<p style=\"margin:0 0 24px;font-size:15px;color:#4B5563;line-height:1.6\">
  Thanks for signing up. Confirm your email to start scanning menus and eating smarter.
</p>
<p style=\"text-align:center;margin:0 0 24px\">
  <a href=\"{{ .ConfirmationURL }}\" style=\"${BUTTON_STYLE}\">Confirm Email</a>
</p>
<p style=\"margin:0;font-size:13px;color:#9CA3AF\">If you didn't create a Fooder account, you can safely ignore this.</p>
${FOOTER}"

# ── Magic Link ───────────────────────────────────────────────
MAGIC_SUBJECT="Your Fooder sign-in link"
MAGIC_BODY="${HEADER}
<h2 style=\"margin:0 0 12px;font-size:22px;color:#1E1E1E\">Sign in to Fooder</h2>
<p style=\"margin:0 0 24px;font-size:15px;color:#4B5563;line-height:1.6\">
  Click below to sign in to your Fooder account. This link expires in 24 hours.
</p>
<p style=\"text-align:center;margin:0 0 24px\">
  <a href=\"{{ .ConfirmationURL }}\" style=\"${BUTTON_STYLE}\">Sign In</a>
</p>
<p style=\"margin:0;font-size:13px;color:#9CA3AF\">If you didn't request this link, you can safely ignore it.</p>
${FOOTER}"

# ── Password Recovery ────────────────────────────────────────
RECOVERY_SUBJECT="Fooder — Reset your password"
RECOVERY_BODY="${HEADER}
<h2 style=\"margin:0 0 12px;font-size:22px;color:#1E1E1E\">Reset your password</h2>
<p style=\"margin:0 0 24px;font-size:15px;color:#4B5563;line-height:1.6\">
  We received a request to reset the password for your Fooder account. Click below to set a new one.
</p>
<p style=\"text-align:center;margin:0 0 24px\">
  <a href=\"{{ .ConfirmationURL }}\" style=\"${BUTTON_STYLE}\">Reset Password</a>
</p>
<p style=\"margin:0;font-size:13px;color:#9CA3AF\">If you didn't request a password reset, no action is needed.</p>
${FOOTER}"

# ── Email Change ─────────────────────────────────────────────
CHANGE_SUBJECT="Fooder — Confirm email change"
CHANGE_BODY="${HEADER}
<h2 style=\"margin:0 0 12px;font-size:22px;color:#1E1E1E\">Confirm your new email</h2>
<p style=\"margin:0 0 24px;font-size:15px;color:#4B5563;line-height:1.6\">
  You requested to change the email address for your Fooder account. Confirm by clicking below.
</p>
<p style=\"text-align:center;margin:0 0 24px\">
  <a href=\"{{ .ConfirmationURL }}\" style=\"${BUTTON_STYLE}\">Confirm New Email</a>
</p>
<p style=\"margin:0;font-size:13px;color:#9CA3AF\">If you didn't request this change, please contact support.</p>
${FOOTER}"

# ── Invite ───────────────────────────────────────────────────
INVITE_SUBJECT="You're invited to Fooder!"
INVITE_BODY="${HEADER}
<h2 style=\"margin:0 0 12px;font-size:22px;color:#1E1E1E\">You're invited to Fooder 🍅</h2>
<p style=\"margin:0 0 24px;font-size:15px;color:#4B5563;line-height:1.6\">
  You've been invited to join Fooder — the smart menu scanning app. Click below to get started.
</p>
<p style=\"text-align:center;margin:0 0 24px\">
  <a href=\"{{ .ConfirmationURL }}\" style=\"${BUTTON_STYLE}\">Accept Invitation</a>
</p>
<p style=\"margin:0;font-size:13px;color:#9CA3AF\">If you weren't expecting this, you can safely ignore it.</p>
${FOOTER}"

# Build JSON payload using jq for proper escaping
PAYLOAD=$(jq -n \
  --arg cs "$CONFIRM_SUBJECT" \
  --arg cb "$CONFIRM_BODY" \
  --arg ms "$MAGIC_SUBJECT" \
  --arg mb "$MAGIC_BODY" \
  --arg rs "$RECOVERY_SUBJECT" \
  --arg rb "$RECOVERY_BODY" \
  --arg es "$CHANGE_SUBJECT" \
  --arg eb "$CHANGE_BODY" \
  --arg is "$INVITE_SUBJECT" \
  --arg ib "$INVITE_BODY" \
  '{
    MAILER_SUBJECTS_CONFIRMATION: $cs,
    MAILER_TEMPLATES_CONFIRMATION_CONTENT: $cb,
    MAILER_SUBJECTS_MAGIC_LINK: $ms,
    MAILER_TEMPLATES_MAGIC_LINK_CONTENT: $mb,
    MAILER_SUBJECTS_RECOVERY: $rs,
    MAILER_TEMPLATES_RECOVERY_CONTENT: $rb,
    MAILER_SUBJECTS_EMAIL_CHANGE: $es,
    MAILER_TEMPLATES_EMAIL_CHANGE_CONTENT: $eb,
    MAILER_SUBJECTS_INVITE: $is,
    MAILER_TEMPLATES_INVITE_CONTENT: $ib,
    SITE_URL: "https://menuocr.app",
    MAILER_SECURE_EMAIL_CHANGE_ENABLED: true,
    MAILER_AUTOCONFIRM: false
  }')

# Send the update
HTTP_CODE=$(curl -s -o /tmp/supabase_email_response.json -w "%{http_code}" \
  -X PATCH "$API" \
  -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

if [[ "$HTTP_CODE" == "200" ]]; then
  echo "✅ Fooder email templates updated successfully!"
  echo "   - Confirm signup: \"${CONFIRM_SUBJECT}\""
  echo "   - Magic link:     \"${MAGIC_SUBJECT}\""
  echo "   - Password reset: \"${RECOVERY_SUBJECT}\""
  echo "   - Email change:   \"${CHANGE_SUBJECT}\""
  echo "   - Invite:         \"${INVITE_SUBJECT}\""
else
  echo "❌ Failed (HTTP ${HTTP_CODE}):"
  cat /tmp/supabase_email_response.json
  echo ""
  echo ""
  echo "If you get 401, make sure your SUPABASE_ACCESS_TOKEN is a valid personal access token"
  echo "from https://supabase.com/dashboard/account/tokens"
  exit 1
fi
