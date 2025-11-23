"""Stripe payment processing router."""

import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
# import stripe  # Temporarily disabled

from app.routers.auth import get_current_user
from app.utils.retry_helper import retry_async, RetryConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY not set - payment features will not work")

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Pydantic models
class PaymentIntentRequest(BaseModel):
    """Request model for creating payment intent."""
    amount: int = Field(..., description="Amount in cents (e.g., 999 for $9.99)")
    currency: str = Field("usd", description="Currency code")
    description: Optional[str] = Field(None, description="Payment description")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")

class PaymentIntentResponse(BaseModel):
    """Response model for payment intent."""
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str

class SubscriptionRequest(BaseModel):
    """Request model for creating subscription."""
    price_id: str = Field(..., description="Stripe price ID")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID")

class SubscriptionResponse(BaseModel):
    """Response model for subscription."""
    subscription_id: str
    client_secret: str
    status: str

class PaymentMethodRequest(BaseModel):
    """Request model for attaching payment method."""
    payment_method_id: str

# In-memory storage for demo (use database in production)
payment_history = {}

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user)
) -> PaymentIntentResponse:
    """
    Create a Stripe payment intent for one-time payments.

    Used for premium OCR processing, advanced features, etc.
    """
    async def _create_intent():
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            description=request.description or f"Menu OCR Premium - {current_user['email']}",
            metadata={
                "user_id": current_user["id"],
                "user_email": current_user["email"],
                **(request.metadata or {})
            },
            automatic_payment_methods={"enabled": True}
        )
        return intent
    
    try:
        # Retry Stripe API call
        intent = await retry_async(_create_intent, config=RetryConfig(delay=10, max_attempts=3))

        # Store in our simple history (use database in production)
        payment_history[intent.id] = {
            "user_id": current_user["id"],
            "amount": request.amount,
            "currency": request.currency,
            "status": intent.status,
            "created_at": datetime.utcnow().isoformat()
        }

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=intent.amount,
            currency=intent.currency,
            status=intent.status
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment intent")

@router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionRequest,
    current_user: dict = Depends(get_current_user)
) -> SubscriptionResponse:
    """
    Create a Stripe subscription for recurring payments.

    Used for premium subscriptions, unlimited OCR, etc.
    """
    async def _create_subscription():
        # Get or create customer
        customers = stripe.Customer.list(email=current_user["email"])
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=current_user["email"],
                metadata={"user_id": current_user["id"]}
            )

        # Create subscription
        subscription_data = {
            "customer": customer.id,
            "items": [{"price": request.price_id}],
            "metadata": {"user_id": current_user["id"]}
        }

        if request.payment_method_id:
            # Attach payment method and set as default
            stripe.PaymentMethod.attach(request.payment_method_id, customer=customer.id)
            stripe.Customer.modify(customer.id, invoice_settings={"default_payment_method": request.payment_method_id})
        else:
            subscription_data["payment_behavior"] = "default_incomplete"
            subscription_data["expand"] = ["latest_invoice.payment_intent"]

        subscription = stripe.Subscription.create(**subscription_data)
        return subscription
    
    try:
        # Retry Stripe API call
        subscription = await retry_async(_create_subscription, config=RetryConfig(delay=10, max_attempts=3))

        return SubscriptionResponse(
            subscription_id=subscription.id,
            client_secret=subscription.latest_invoice.payment_intent.client_secret if hasattr(subscription.latest_invoice, 'payment_intent') and subscription.latest_invoice.payment_intent else "",
            status=subscription.status
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe subscription error: {e}")
        raise HTTPException(status_code=400, detail=f"Subscription error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Stripe webhooks for payment events.

    Processes payment confirmations, failures, subscription changes, etc.
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not STRIPE_WEBHOOK_SECRET:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured - webhook verification disabled")
            event = json.loads(payload)
        else:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
            except ValueError as e:
                logger.error(f"Invalid webhook payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid webhook signature: {e}")
                raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle different event types
        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing webhook event: {event_type}")

        if event_type == "payment_intent.succeeded":
            await handle_payment_success(event_data, background_tasks)
        elif event_type == "payment_intent.payment_failed":
            await handle_payment_failure(event_data, background_tasks)
        elif event_type.startswith("customer.subscription"):
            await handle_subscription_event(event_type, event_data, background_tasks)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.get("/history")
async def get_payment_history(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's payment history.

    Returns payment intents and subscription information.
    """
    async def _fetch_history():
        # Get payment intents from Stripe
        payment_intents = stripe.PaymentIntent.list(
            customer=current_user.get("stripe_customer_id"),
            limit=50
        )

        # Get subscriptions
        subscriptions = stripe.Subscription.list(
            customer=current_user.get("stripe_customer_id"),
            limit=50
        )
        
        return payment_intents, subscriptions
    
    try:
        # Retry Stripe API calls
        payment_intents, subscriptions = await retry_async(_fetch_history, config=RetryConfig(delay=10, max_attempts=3))

        return {
            "payment_intents": [
                {
                    "id": pi.id,
                    "amount": pi.amount,
                    "currency": pi.currency,
                    "status": pi.status,
                    "created": pi.created,
                    "description": pi.description
                }
                for pi in payment_intents.data
            ],
            "subscriptions": [
                {
                    "id": sub.id,
                    "status": sub.status,
                    "current_period_start": sub.current_period_start,
                    "current_period_end": sub.current_period_end,
                    "items": [
                        {
                            "price": {
                                "id": item.price.id,
                                "nickname": item.price.nickname,
                                "unit_amount": item.price.unit_amount,
                                "currency": item.price.currency
                            }
                        }
                        for item in sub.items.data
                    ]
                }
                for sub in subscriptions.data
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch payment history")

async def handle_payment_success(payment_intent: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle successful payment."""
    payment_id = payment_intent["id"]
    user_id = payment_intent.get("metadata", {}).get("user_id")

    if user_id:
        # Update user's premium status in database
        # This would typically update a user record in Supabase
        logger.info(f"Payment successful for user {user_id}: {payment_id}")

        # Update our simple history
        if payment_id in payment_history:
            payment_history[payment_id]["status"] = "succeeded"

async def handle_payment_failure(payment_intent: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle failed payment."""
    payment_id = payment_intent["id"]
    user_id = payment_intent.get("metadata", {}).get("user_id")

    logger.warning(f"Payment failed for user {user_id}: {payment_id}")

    # Update our simple history
    if payment_id in payment_history:
        payment_history[payment_id]["status"] = "failed"

async def handle_subscription_event(event_type: str, subscription: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle subscription events."""
    user_id = subscription.get("metadata", {}).get("user_id")
    subscription_id = subscription["id"]
    status = subscription["status"]

    logger.info(f"Subscription {event_type} for user {user_id}: {subscription_id} - {status}")

    # Update user's subscription status in database
    # This would typically update a user record in Supabase