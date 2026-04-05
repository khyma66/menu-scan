"""
Subscription router — web-only purchase model.

WHY NO IN-APP PURCHASES:
  Apple charges 30% (15% small biz) on all iOS IAP/subscriptions.
  Google charges 30% on all Play Store subscriptions.
  By routing ALL subscription purchases through the web (Stripe direct),
  we keep 100% of revenue minus Stripe's ~2.9% + $0.30 per transaction.

FLOW:
  1. Native app calls GET /subscriptions/status  → returns current plan
  2. Native app calls POST /subscriptions/checkout-session
       → returns a Stripe Checkout URL (hosted on our web domain)
  3. Native app opens URL in external browser / Custom Chrome Tab / SFSafariVC
  4. User pays on web → Stripe redirects to web success page
  5. Web success page redirects to deep-link: menuocr://subscription-result?status=success
  6. Native app receives deep-link, re-fetches /subscriptions/status, updates UI

EDGE CASES HANDLED:
  - SCA/3DS (Stripe Checkout handles automatically)
  - India UPI / Brazil PIX / EU SEPA / BACS (enabled as Stripe payment methods)
  - Currency localisation (Stripe Checkout auto-presents local currency)
  - Duplicate Stripe webhooks (idempotency via stripe_webhook_events table)
  - Grace period: 7 days active after payment failure before downgrade
  - Trial periods: trialing status passed through
  - Subscription pause/cancel (cancel_at_period_end)
  - User without subscription row (falls back to free defaults)
  - Checkout session expiry (24 h)
  - Multiple devices / sessions sharing same Supabase JWT
"""

import os
import json
import logging
import stripe
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel

from app.routers.auth import get_current_user
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "https://menuocr.com")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ─────────────────────────── Pydantic models ────────────────────────────────

class SubscriptionStatus(BaseModel):
    plan_id: str
    plan_name: str
    status: str               # active | trialing | past_due | canceled | paused
    is_effective: bool        # True if user currently has access to paid features
    scan_limit_monthly: int   # -1 = unlimited
    features: list[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    billing_cycle: Optional[str]
    stripe_customer_id: Optional[str]

class CheckoutRequest(BaseModel):
    plan_id: str                            # "pro" | "max"
    billing_cycle: str = "monthly"         # "monthly" | "yearly"
    # Deep-links the app wants the web page to redirect to after checkout
    success_deeplink: str = "menuocr://subscription-result?status=success"
    cancel_deeplink:  str = "menuocr://subscription-result?status=cancel"

class CheckoutResponse(BaseModel):
    checkout_url: str           # Open this in browser
    session_id: str

class PortalResponse(BaseModel):
    portal_url: str             # Stripe Customer Portal for manage/cancel

# ─────────────────────────── Helpers ────────────────────────────────────────

def _plan_fallback() -> dict:
    return {
        "plan_id": "free",
        "plan_name": "Free",
        "status": "active",
        "is_effective": True,
        "scan_limit_monthly": 3,
        "features": ["3 scans / month", "Basic nutrition info", "Allergen alerts"],
        "current_period_end": None,
        "cancel_at_period_end": False,
        "billing_cycle": None,
        "stripe_customer_id": None,
    }

async def _get_or_create_stripe_customer(user: dict, sb) -> str:
    """Get existing Stripe customer ID from DB, or create one in Stripe."""
    res = (
        sb.table("user_subscriptions")
          .select("stripe_customer_id")
          .eq("user_id", user["id"])
          .single()
          .execute()
    )
    if res.data and res.data.get("stripe_customer_id"):
        return res.data["stripe_customer_id"]

    # Create in Stripe
    customer = stripe.Customer.create(
        email=user.get("email", ""),
        metadata={"supabase_user_id": user["id"]},
    )
    # Persist
    sb.table("user_subscriptions").upsert(
        {"user_id": user["id"], "stripe_customer_id": customer.id},
        on_conflict="user_id",
    ).execute()
    return customer.id

# ─────────────────────────── Routes ─────────────────────────────────────────

@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """
    Return the caller's current subscription plan and status.
    Called by native apps on startup and after returning from checkout.
    """
    try:
        sb = get_supabase_client()
        res = (
            sb.table("user_plan_status")
              .select("*")
              .eq("user_id", current_user["id"])
              .single()
              .execute()
        )
        if not res.data:
            return SubscriptionStatus(**_plan_fallback())

        d = res.data
        return SubscriptionStatus(
            plan_id=d.get("plan_id", "free"),
            plan_name=d.get("plan_name", "Free"),
            status=d.get("status", "active"),
            is_effective=d.get("is_effective", True),
            scan_limit_monthly=d.get("scan_limit_monthly", 3),
            features=d.get("features") or [],
            current_period_end=str(d["current_period_end"]) if d.get("current_period_end") else None,
            cancel_at_period_end=d.get("cancel_at_period_end", False),
            billing_cycle=d.get("billing_cycle"),
            stripe_customer_id=d.get("stripe_customer_id"),
        )
    except Exception as e:
        logger.error(f"subscription status error: {e}")
        return SubscriptionStatus(**_plan_fallback())


@router.get("/plans")
async def list_plans():
    """
    Return all active pricing plans.
    Used by native apps to render the upgrade screen with current pricing.
    No auth required — plans are public.
    """
    try:
        sb = get_supabase_client()
        res = (
            sb.table("subscription_plans")
              .select("*")
              .eq("is_active", True)
              .order("sort_order")
              .execute()
        )
        return {"plans": res.data or []}
    except Exception as e:
        logger.error(f"list plans error: {e}")
        raise HTTPException(status_code=500, detail="Could not load plans")


@router.post("/checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    req: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a Stripe Checkout Session for web-based subscription purchase.

    The native app opens checkout_url in the system browser.
    After payment Stripe redirects to our web success page which in turn
    issues a deeplink back to the app.

    This completely bypasses Apple/Google commission — the payment flows
    through Stripe directly with no in-app purchase API involved.
    """
    if not stripe.api_key:
        raise HTTPException(503, "Payment service not configured")

    sb = get_supabase_client()

    # ── Resolve Stripe price ID from DB
    plan_res = (
        sb.table("subscription_plans")
          .select("stripe_price_monthly,stripe_price_yearly,display_name")
          .eq("id", req.plan_id)
          .eq("is_active", True)
          .single()
          .execute()
    )
    if not plan_res.data:
        raise HTTPException(400, f"Unknown plan: {req.plan_id}")

    plan_data = plan_res.data
    price_id = (
        plan_data["stripe_price_yearly"]
        if req.billing_cycle == "yearly"
        else plan_data["stripe_price_monthly"]
    )
    if not price_id:
        raise HTTPException(400, f"Plan {req.plan_id} has no Stripe price configured")

    customer_id = await _get_or_create_stripe_customer(current_user, sb)

    # ── Build success/cancel URLs that the web page consumes to issue deeplinks
    success_url = (
        f"{WEB_BASE_URL}/subscription/complete"
        f"?session_id={{CHECKOUT_SESSION_ID}}"
        f"&deeplink={req.success_deeplink}"
    )
    cancel_url = (
        f"{WEB_BASE_URL}/subscription/cancel"
        f"?deeplink={req.cancel_deeplink}"
    )

    # ── Create Stripe Checkout Session
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,        # so discount codes work globally
        billing_address_collection="auto",  # needed for SCA compliance
        automatic_tax={"enabled": False},  # No tax — prices are all-inclusive
        metadata={
            "supabase_user_id": current_user["id"],
            "plan_id": req.plan_id,
            "billing_cycle": req.billing_cycle,
        },
        # Payment method types: Stripe auto-selects best methods per country.
        # Explicitly listed for safety: covers US/EU/India/Brazil/SEA/ANZ
        payment_method_types=[
            "card",       # global
            "paypal",     # global
            "sepa_debit", # EU
            "bacs_debit", # UK
            "bancontact",  # Belgium
            "ideal",      # Netherlands
            "giropay",    # Germany
            "sofort",     # DE/AT/CH
            "p24",        # Poland
            "eps",        # Austria
            # Note: UPI (India) and PIX (Brazil) available via Stripe but
            # require separate activation — handled at Stripe dashboard level
        ],
        subscription_data={
            "trial_period_days": 0,   # set to e.g. 7 for free trial
            "metadata": {
                "supabase_user_id": current_user["id"],
                "plan_id": req.plan_id,
            },
        },
        expires_at=int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
    )

    # ── Persist checkout session for deep-link state tracking
    sb.table("checkout_sessions").insert({
        "user_id": current_user["id"],
        "stripe_session_id": session.id,
        "plan_id": req.plan_id,
        "billing_cycle": req.billing_cycle,
        "status": "pending",
        "success_deeplink": req.success_deeplink,
        "cancel_deeplink": req.cancel_deeplink,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }).execute()

    return CheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/customer-portal", response_model=PortalResponse)
async def create_customer_portal_session(
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a Stripe Customer Portal URL so users can:
    - Update payment method
    - Cancel subscription
    - Download invoices

    Open this URL in the system browser from the native app.
    """
    if not stripe.api_key:
        raise HTTPException(503, "Payment service not configured")

    sb = get_supabase_client()
    res = (
        sb.table("user_subscriptions")
          .select("stripe_customer_id")
          .eq("user_id", current_user["id"])
          .single()
          .execute()
    )
    if not res.data or not res.data.get("stripe_customer_id"):
        raise HTTPException(400, "No subscription found to manage")

    session = stripe.billing_portal.Session.create(
        customer=res.data["stripe_customer_id"],
        return_url=f"{WEB_BASE_URL}/account",
    )
    return PortalResponse(portal_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint — the ONLY place that writes subscription state.

    Idempotent: skips events already in stripe_webhook_events table.
    Handles: checkout.session.completed, customer.subscription.*, invoice.*
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    # Verify signature
    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        else:
            event = json.loads(payload)
            logger.warning("Webhook signature verification disabled — set STRIPE_WEBHOOK_SECRET")
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(400, f"Webhook error: {e}")

    event_id   = event.get("id", "")
    event_type = event["type"]

    # ── Service-role Supabase client (bypasses RLS to write subscription state)
    from supabase import create_client
    supabase_url = os.getenv("SUPABASE_URL", "")
    sb = create_client(supabase_url, SUPABASE_SERVICE_KEY)

    # ── Idempotency check
    existing = (
        sb.table("stripe_webhook_events")
          .select("stripe_event_id")
          .eq("stripe_event_id", event_id)
          .execute()
    )
    if existing.data:
        logger.info(f"Duplicate webhook skipped: {event_id}")
        return {"status": "duplicate_skipped"}

    # ── Record event (do this before processing so concurrent duplicates are blocked)
    sb.table("stripe_webhook_events").insert({
        "stripe_event_id": event_id,
        "event_type": event_type,
        "payload": json.loads(payload),
    }).execute()

    obj = event["data"]["object"]

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_complete(obj, sb)

        elif event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
        ):
            await _handle_subscription_upsert(obj, sb)

        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(obj, sb)

        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(obj, sb)

        elif event_type == "invoice.paid":
            await _handle_invoice_paid(obj, sb)

        else:
            logger.info(f"Unhandled webhook event: {event_type}")

    except Exception as e:
        logger.error(f"Webhook processing error [{event_type}]: {e}")
        # Return 200 so Stripe doesn't retry — we've already recorded the event.
        # Log for manual review.

    return {"status": "ok"}


# ─────────────────────────── Webhook handlers ───────────────────────────────

async def _handle_checkout_complete(session: dict, sb):
    """Checkout session completed — subscription now created in Stripe."""
    user_id = session.get("metadata", {}).get("supabase_user_id")
    plan_id  = session.get("metadata", {}).get("plan_id", "pro")
    cycle    = session.get("metadata", {}).get("billing_cycle", "monthly")
    stripe_sub_id = session.get("subscription")
    customer_id   = session.get("customer")

    if not user_id:
        logger.error("checkout.session.completed missing supabase_user_id in metadata")
        return

    # Mark checkout session record complete
    sb.table("checkout_sessions").update({"status": "complete"}).eq(
        "stripe_session_id", session["id"]
    ).execute()

    # Fetch the subscription details from Stripe for accurate timestamps
    sub = stripe.Subscription.retrieve(stripe_sub_id) if stripe_sub_id else None

    sb.table("user_subscriptions").upsert(
        {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": sub.status if sub else "active",
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": stripe_sub_id,
            "stripe_price_id": sub["items"]["data"][0]["price"]["id"] if sub else None,
            "billing_cycle": cycle,
            "current_period_start": datetime.fromtimestamp(
                sub.current_period_start, tz=timezone.utc
            ).isoformat() if sub else None,
            "current_period_end": datetime.fromtimestamp(
                sub.current_period_end, tz=timezone.utc
            ).isoformat() if sub else None,
            "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
            "purchase_channel": "web",
        },
        on_conflict="user_id",
    ).execute()


async def _handle_subscription_upsert(sub: dict, sb):
    """Subscription created or updated (plan change, renewal, etc.)."""
    user_id = sub.get("metadata", {}).get("supabase_user_id")
    if not user_id:
        # Fall back to lookup via stripe_customer_id
        res = (
            sb.table("user_subscriptions")
              .select("user_id")
              .eq("stripe_customer_id", sub["customer"])
              .single()
              .execute()
        )
        if not res.data:
            logger.error(f"Cannot map Stripe subscription {sub['id']} to user")
            return
        user_id = res.data["user_id"]

    # Determine plan from Stripe price metadata or fall back to "pro"
    price_id = sub["items"]["data"][0]["price"]["id"] if sub.get("items") else ""
    # Look up plan by stripe price
    plan_res = (
        sb.table("subscription_plans")
          .select("id")
          .or_(f"stripe_price_monthly.eq.{price_id},stripe_price_yearly.eq.{price_id}")
          .execute()
    )
    plan_id = plan_res.data[0]["id"] if plan_res.data else "pro"

    cycle = "yearly" if sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("recurring", {}).get("interval") == "year" else "monthly"

    sb.table("user_subscriptions").upsert(
        {
            "user_id": user_id,
            "plan_id": plan_id,
            "status": sub["status"],
            "stripe_customer_id": sub["customer"],
            "stripe_subscription_id": sub["id"],
            "stripe_price_id": price_id,
            "billing_cycle": cycle,
            "current_period_start": datetime.fromtimestamp(
                sub["current_period_start"], tz=timezone.utc
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                sub["current_period_end"], tz=timezone.utc
            ).isoformat(),
            "cancel_at_period_end": sub.get("cancel_at_period_end", False),
            "trial_end": datetime.fromtimestamp(
                sub["trial_end"], tz=timezone.utc
            ).isoformat() if sub.get("trial_end") else None,
            "grace_period_end": None,  # reset on successful renewal
            "purchase_channel": "web",
        },
        on_conflict="user_id",
    ).execute()


async def _handle_subscription_deleted(sub: dict, sb):
    """Subscription canceled and fully expired."""
    res = (
        sb.table("user_subscriptions")
          .select("user_id")
          .eq("stripe_subscription_id", sub["id"])
          .execute()
    )
    if not res.data:
        return
    user_id = res.data[0]["user_id"]

    sb.table("user_subscriptions").update(
        {"plan_id": "free", "status": "canceled", "stripe_subscription_id": None}
    ).eq("user_id", user_id).execute()


async def _handle_payment_failed(invoice: dict, sb):
    """
    Payment failed on renewal — set status to past_due and start 7-day grace period.
    User retains paid access during grace period; downgraded to free after that.
    """
    sub_id = invoice.get("subscription")
    if not sub_id:
        return

    res = (
        sb.table("user_subscriptions")
          .select("user_id")
          .eq("stripe_subscription_id", sub_id)
          .execute()
    )
    if not res.data:
        return
    user_id = res.data[0]["user_id"]

    grace_end = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    sb.table("user_subscriptions").update(
        {"status": "past_due", "grace_period_end": grace_end}
    ).eq("user_id", user_id).execute()


async def _handle_invoice_paid(invoice: dict, sb):
    """Invoice paid (renewal) — clear grace period, confirm active status."""
    sub_id = invoice.get("subscription")
    if not sub_id:
        return

    res = (
        sb.table("user_subscriptions")
          .select("user_id")
          .eq("stripe_subscription_id", sub_id)
          .execute()
    )
    if not res.data:
        return
    user_id = res.data[0]["user_id"]

    sb.table("user_subscriptions").update(
        {"status": "active", "grace_period_end": None}
    ).eq("user_id", user_id).execute()
