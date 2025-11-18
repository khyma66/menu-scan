"""Enhanced pricing plans management router."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from app.routers.auth import get_current_user
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pricing", tags=["Pricing Plans"])

# Pricing Plan models
class PricingPlan(BaseModel):
    """Response model for pricing plan."""
    id: str
    name: str
    description: str
    price_monthly_cents: int
    price_yearly_cents: Optional[int]
    stripe_price_id_monthly: str
    stripe_price_id_yearly: Optional[str]
    features: List[str]
    is_active: bool

class PlanSubscriptionRequest(BaseModel):
    """Request model for subscribing to a plan."""
    plan_id: str = Field(..., description="Plan ID to subscribe to")
    billing_cycle: str = Field("monthly", description="Billing cycle: monthly or yearly")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")

class PlanSubscriptionResponse(BaseModel):
    """Response model for plan subscription."""
    subscription_id: str
    client_secret: Optional[str]
    status: str
    plan_name: str
    billing_cycle: str
    amount: int

class SubscriptionCancelRequest(BaseModel):
    """Request model for canceling subscription."""
    cancel_at_period_end: bool = Field(True, description="Cancel at end of current period")

class CurrentSubscription(BaseModel):
    """Response model for current subscription."""
    plan_name: str
    plan_description: str
    status: str
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    features: List[str]
    billing_cycle: str
    amount: int

@router.get("/plans", response_model=List[PricingPlan])
async def get_pricing_plans(active_only: bool = Query(True, description="Only return active plans")):
    """Get all available pricing plans."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("pricing_plans").select("*")
        
        if active_only:
            query = query.eq("is_active", True)
        
        response = query.order("price_monthly_cents").execute()
        
        if not response.data:
            return []
        
        # Convert to response model format
        plans = []
        for plan in response.data:
            plans.append(PricingPlan(
                id=plan["id"],
                name=plan["name"],
                description=plan["description"],
                price_monthly_cents=plan["price_monthly_cents"],
                price_yearly_cents=plan.get("price_yearly_cents"),
                stripe_price_id_monthly=plan["stripe_price_id_monthly"],
                stripe_price_id_yearly=plan.get("stripe_price_id_yearly"),
                features=plan.get("features", []),
                is_active=plan["is_active"]
            ))
        
        return plans
    except Exception as e:
        logger.error(f"Error getting pricing plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe", response_model=PlanSubscriptionResponse)
async def subscribe_to_plan(
    request: PlanSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Subscribe to a pricing plan."""
    try:
        import stripe
        from app.services.supabase_client import get_supabase_client
        
        # Initialize Stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get plan details
        plan_response = supabase.table("pricing_plans").select("*").eq("id", request.plan_id).eq("is_active", True).single().execute()
        
        if not plan_response.data:
            raise HTTPException(status_code=404, detail="Plan not found or inactive")
        
        plan = plan_response.data
        
        # Get or create Stripe customer
        customers = stripe.Customer.list(email=current_user["email"])
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=current_user["email"],
                metadata={"user_id": user_id}
            )
        
        # Update user with Stripe customer ID
        supabase.table("users").update({"stripe_customer_id": customer.id}).eq("id", user_id).execute()
        
        # Get price ID based on billing cycle
        price_id = plan["stripe_price_id_monthly"]
        amount = plan["price_monthly_cents"]
        
        if request.billing_cycle == "yearly" and plan.get("stripe_price_id_yearly"):
            price_id = plan["stripe_price_id_yearly"]
            amount = plan["price_yearly_cents"] or plan["price_monthly_cents"]
        
        # Create subscription
        subscription_data = {
            "customer": customer.id,
            "items": [{"price": price_id}],
            "metadata": {"user_id": user_id, "plan_id": request.plan_id},
            "payment_behavior": "default_incomplete",
            "expand": ["latest_invoice.payment_intent"]
        }
        
        if request.payment_method_id:
            # Attach payment method
            stripe.PaymentMethod.attach(request.payment_method_id, customer=customer.id)
            stripe.Customer.modify(customer.id, invoice_settings={"default_payment_method": request.payment_method_id})
        
        subscription = stripe.Subscription.create(**subscription_data)
        
        # Store subscription in database
        subscription_db_data = {
            "user_id": user_id,
            "plan_id": request.plan_id,
            "stripe_subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end
        }
        
        supabase.table("user_subscriptions").insert(subscription_db_data).execute()
        
        # Update user's subscription status
        supabase.table("users").update({
            "subscription_plan": plan["name"].lower(),
            "subscription_status": subscription.status
        }).eq("id", user_id).execute()
        
        return PlanSubscriptionResponse(
            subscription_id=subscription.id,
            client_secret=subscription.latest_invoice.payment_intent.client_secret if hasattr(subscription.latest_invoice, 'payment_intent') and subscription.latest_invoice.payment_intent else "",
            status=subscription.status,
            plan_name=plan["name"],
            billing_cycle=request.billing_cycle,
            amount=amount
        )
        
    except Exception as e:
        logger.error(f"Error subscribing to plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    current_user: dict = Depends(get_current_user)
):
    """Cancel user's subscription."""
    try:
        import stripe
        from app.services.supabase_client import get_supabase_client
        
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get user's current subscription
        subscription_response = supabase.table("user_subscriptions").select("stripe_subscription_id").eq("user_id", user_id).eq("status", "active").single().execute()
        
        if not subscription_response.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        stripe_subscription_id = subscription_response.data["stripe_subscription_id"]
        
        # Cancel subscription in Stripe
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=request.cancel_at_period_end
        )
        
        # Update subscription in database
        supabase.table("user_subscriptions").update({
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "status": subscription.status
        }).eq("stripe_subscription_id", stripe_subscription_id).execute()
        
        # Update user's subscription status
        supabase.table("users").update({
            "subscription_status": subscription.status
        }).eq("id", user_id).execute()
        
        return {"message": "Subscription cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current-subscription", response_model=CurrentSubscription)
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's current subscription details."""
    try:
        from app.services.supabase_client import get_supabase_client
        
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get user subscription with plan details
        response = supabase.table("user_subscriptions").select("""
            *,
            pricing_plans(name, description, features, price_monthly_cents, price_yearly_cents)
        """).eq("user_id", user_id).execute()
        
        if not response.data:
            # User doesn't have a subscription, return free plan
            return CurrentSubscription(
                plan_name="Free",
                plan_description="Free plan with limited features",
                status="active",
                current_period_end=None,
                cancel_at_period_end=False,
                features=["100 OCR scans per month", "Basic dish analysis", "Email support"],
                billing_cycle="monthly",
                amount=0
            )
        
        subscription = response.data[0]
        plan = subscription["pricing_plans"]
        
        # Determine billing cycle and amount (simplified - you might want to store this in DB)
        billing_cycle = "monthly"
        amount = plan["price_monthly_cents"]
        
        return CurrentSubscription(
            plan_name=plan["name"],
            plan_description=plan["description"],
            status=subscription["status"],
            current_period_end=subscription.get("current_period_end"),
            cancel_at_period_end=subscription.get("cancel_at_period_end", False),
            features=plan.get("features", []),
            billing_cycle=billing_cycle,
            amount=amount
        )
        
    except Exception as e:
        logger.error(f"Error getting current subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-setup-intent")
async def create_setup_intent(current_user: dict = Depends(get_current_user)):
    """Create a setup intent for adding payment method."""
    try:
        import stripe
        
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        # Get or create Stripe customer
        customers = stripe.Customer.list(email=current_user["email"])
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=current_user["email"],
                metadata={"user_id": current_user.get("id")}
            )
        
        # Create setup intent
        setup_intent = stripe.SetupIntent.create(
            customer=customer.id,
            payment_method_types=["card"],
        )
        
        return {
            "client_secret": setup_intent.client_secret,
            "customer_id": customer.id
        }
        
    except Exception as e:
        logger.error(f"Error creating setup intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))