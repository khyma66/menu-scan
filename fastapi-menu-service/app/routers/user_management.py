"""Enhanced user profile and settings management router."""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timedelta

from app.routers.auth import get_current_user
from app.services.auth_service import AuthService
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User Management"])

auth_service = AuthService()

# Address models
class AddressCreate(BaseModel):
    """Request model for creating address."""
    type: str = Field("home", description="Address type: home, work, delivery")
    street: str = Field(..., description="Street address")
    apartment_number: Optional[str] = Field(None, description="Apartment/unit number")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    zip_code: str = Field(..., description="ZIP/Postal code")
    country: str = Field("US", description="Country code")
    is_primary: bool = Field(False, description="Set as primary address")

class AddressUpdate(BaseModel):
    """Request model for updating address."""
    type: Optional[str] = None
    street: Optional[str] = None
    apartment_number: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    is_primary: Optional[bool] = None

class AddressResponse(BaseModel):
    """Response model for address."""
    id: str
    type: str
    street: str
    apartment_number: Optional[str]
    city: str
    state: str
    zip_code: str
    country: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

# Password change models
class PasswordChangeRequest(BaseModel):
    """Request model for password change."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")

class PasswordChangeResponse(BaseModel):
    """Response model for password change."""
    message: str
    password_changed_at: datetime

# Referral models
class ReferralInfo(BaseModel):
    """Response model for referral information."""
    referral_code: str
    referral_count: int
    referral_link: str
    pending_referrals: List[Dict[str, Any]]

class ReferralCreate(BaseModel):
    """Request model for creating referral."""
    referral_code: str = Field(..., description="Referral code to use")

# User subscription models
class UserSubscriptionInfo(BaseModel):
    """Response model for user subscription info."""
    plan_name: str
    plan_description: str
    status: str
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool

# User profile models
class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    address_country: Optional[str] = None


class AppProfileDetailsRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None


class AppProfileDetailsResponse(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    updated_at: Optional[str] = None


class DiscoveryPreferencesRequest(BaseModel):
    search_radius_miles: Optional[int] = Field(default=10, ge=1, le=50)
    selected_cuisines: Optional[List[str]] = Field(default_factory=list)
    location_label: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DiscoveryPreferencesResponse(BaseModel):
    user_id: str
    search_radius_miles: int = 10
    selected_cuisines: List[str] = Field(default_factory=list)
    location_label: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    updated_at: Optional[str] = None


class ProfilePreferencesRequest(BaseModel):
    notifications_enabled: Optional[bool] = True
    push_notifications: Optional[bool] = True
    email_notifications: Optional[bool] = False
    profile_visibility: Optional[str] = "private"
    analytics_opt_in: Optional[bool] = True
    marketing_opt_in: Optional[bool] = False
    language: Optional[str] = None
    timezone: Optional[str] = None


class ProfilePreferencesResponse(BaseModel):
    user_id: str
    notifications_enabled: bool = True
    push_notifications: bool = True
    email_notifications: bool = False
    profile_visibility: str = "private"
    analytics_opt_in: bool = True
    marketing_opt_in: bool = False
    language: Optional[str] = None
    timezone: Optional[str] = None
    updated_at: Optional[str] = None


class SavedCardRequest(BaseModel):
    card_brand: str
    card_last_four: str = Field(..., min_length=4, max_length=4)
    card_exp_month: int = Field(..., ge=1, le=12)
    card_exp_year: int = Field(..., ge=2024)
    cardholder_name: Optional[str] = None
    tokenized_card_id: Optional[str] = None
    is_default: bool = True


class SavedCardResponse(BaseModel):
    id: str
    card_brand: str
    card_last_four: str
    card_exp_month: int
    card_exp_year: int
    cardholder_name: Optional[str] = None
    is_default: bool = False
    created_at: Optional[str] = None


class SavedCardsListResponse(BaseModel):
    cards: List[SavedCardResponse]


class UserPaymentRecordResponse(BaseModel):
    id: str
    amount_cents: int
    currency: str
    status: str
    transaction_type: str
    created_at: Optional[str] = None


class UserPaymentHistoryResponse(BaseModel):
    payments: List[UserPaymentRecordResponse]


class SubscriptionPlanInfo(BaseModel):
    name: str
    price_display: str
    billing_period: str
    description: str
    features: List[str] = Field(default_factory=list)


class SubscriptionPlansResponse(BaseModel):
    plans: List[SubscriptionPlanInfo]


class SelectSubscriptionPlanRequest(BaseModel):
    plan_name: str


@router.get("/app-profile", response_model=AppProfileDetailsResponse)
async def get_app_profile(current_user: dict = Depends(get_current_user)):
    """Get app profile details used by mobile profile tabs."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        profile_response = supabase.table("user_profile_details").select("*").eq("user_id", user_id).limit(1).execute()
        profile = (profile_response.data or [{}])[0]

        return AppProfileDetailsResponse(
            user_id=user_id,
            full_name=profile.get("full_name"),
            email=profile.get("email") or current_user.get("email"),
            contact=profile.get("contact"),
            phone=profile.get("phone"),
            country=profile.get("country"),
            updated_at=profile.get("updated_at"),
        )
    except Exception as e:
        logger.error(f"Error getting app profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/app-profile", response_model=AppProfileDetailsResponse)
async def update_app_profile(
    profile: AppProfileDetailsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Upsert app profile details used by mobile profile tabs."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        payload = {
            "user_id": user_id,
            "full_name": profile.full_name,
            "email": profile.email,
            "contact": profile.contact,
            "phone": profile.phone,
            "country": profile.country,
            "updated_at": datetime.utcnow().isoformat(),
        }

        supabase.table("user_profile_details").upsert(payload, {"on_conflict": "user_id"}).execute()

        # Keep users table in sync for common fields if available
        users_update = {}
        if profile.full_name is not None:
            users_update["full_name"] = profile.full_name
        if profile.phone is not None:
            users_update["phone"] = profile.phone
        if profile.email is not None:
            users_update["email"] = profile.email
        if users_update:
            users_update["updated_at"] = datetime.utcnow().isoformat()
            supabase.table("users").upsert({"id": user_id, **users_update}, {"on_conflict": "id"}).execute()

        return await get_app_profile(current_user)
    except Exception as e:
        logger.error(f"Error updating app profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discovery-preferences", response_model=DiscoveryPreferencesResponse)
async def get_discovery_preferences(current_user: dict = Depends(get_current_user)):
    """Get persisted discovery tab preferences."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        response = supabase.table("user_discovery_preferences").select("*").eq("user_id", user_id).limit(1).execute()
        row = (response.data or [{}])[0]

        return DiscoveryPreferencesResponse(
            user_id=user_id,
            search_radius_miles=row.get("search_radius_miles", 10),
            selected_cuisines=row.get("selected_cuisines") or [],
            location_label=row.get("location_label"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            updated_at=row.get("updated_at"),
        )
    except Exception as e:
        logger.error(f"Error getting discovery preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/discovery-preferences", response_model=DiscoveryPreferencesResponse)
async def update_discovery_preferences(
    preferences: DiscoveryPreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    """Persist discovery tab preferences."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        payload = {
            "user_id": user_id,
            "search_radius_miles": preferences.search_radius_miles or 10,
            "selected_cuisines": preferences.selected_cuisines or [],
            "location_label": preferences.location_label,
            "latitude": preferences.latitude,
            "longitude": preferences.longitude,
            "updated_at": datetime.utcnow().isoformat(),
        }

        supabase.table("user_discovery_preferences").upsert(payload, {"on_conflict": "user_id"}).execute()

        return await get_discovery_preferences(current_user)
    except Exception as e:
        logger.error(f"Error updating discovery preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile-preferences", response_model=ProfilePreferencesResponse)
async def get_profile_preferences(current_user: dict = Depends(get_current_user)):
    """Get profile preferences for notifications and privacy subtabs."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        response = supabase.table("user_profile_preferences").select("*").eq("user_id", user_id).limit(1).execute()
        row = (response.data or [{}])[0]

        return ProfilePreferencesResponse(
            user_id=user_id,
            notifications_enabled=row.get("notifications_enabled", True),
            push_notifications=row.get("push_notifications", True),
            email_notifications=row.get("email_notifications", False),
            profile_visibility=row.get("profile_visibility", "private"),
            analytics_opt_in=row.get("analytics_opt_in", True),
            marketing_opt_in=row.get("marketing_opt_in", False),
            language=row.get("language"),
            timezone=row.get("timezone"),
            updated_at=row.get("updated_at"),
        )
    except Exception as e:
        logger.error(f"Error getting profile preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile-preferences", response_model=ProfilePreferencesResponse)
async def update_profile_preferences(
    preferences: ProfilePreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update profile preferences for notifications and privacy subtabs."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        payload = {
            "user_id": user_id,
            "notifications_enabled": preferences.notifications_enabled,
            "push_notifications": preferences.push_notifications,
            "email_notifications": preferences.email_notifications,
            "profile_visibility": preferences.profile_visibility,
            "analytics_opt_in": preferences.analytics_opt_in,
            "marketing_opt_in": preferences.marketing_opt_in,
            "language": preferences.language,
            "timezone": preferences.timezone,
            "updated_at": datetime.utcnow().isoformat(),
        }

        supabase.table("user_profile_preferences").upsert(payload, {"on_conflict": "user_id"}).execute()
        return await get_profile_preferences(current_user)
    except Exception as e:
        logger.error(f"Error updating profile preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved-cards", response_model=SavedCardsListResponse)
async def get_saved_cards(current_user: dict = Depends(get_current_user)):
    """Get saved card metadata for payment subtab."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        response = supabase.table("user_saved_cards").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        cards = response.data or []

        return SavedCardsListResponse(cards=[
            SavedCardResponse(
                id=row.get("id"),
                card_brand=row.get("card_brand", "card"),
                card_last_four=row.get("card_last_four", "0000"),
                card_exp_month=row.get("card_exp_month", 1),
                card_exp_year=row.get("card_exp_year", datetime.utcnow().year),
                cardholder_name=row.get("cardholder_name"),
                is_default=row.get("is_default", False),
                created_at=row.get("created_at"),
            )
            for row in cards
        ])
    except Exception as e:
        logger.error(f"Error getting saved cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/saved-cards", response_model=SavedCardResponse)
async def save_card(
    card: SavedCardRequest,
    current_user: dict = Depends(get_current_user),
):
    """Store masked card metadata with tokenized reference."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        if card.is_default:
            supabase.table("user_saved_cards").update({"is_default": False}).eq("user_id", user_id).execute()

        payload = {
            "user_id": user_id,
            "card_brand": card.card_brand.lower(),
            "card_last_four": card.card_last_four,
            "card_exp_month": card.card_exp_month,
            "card_exp_year": card.card_exp_year,
            "cardholder_name": card.cardholder_name,
            "tokenized_card_id": card.tokenized_card_id,
            "is_default": card.is_default,
        }

        response = supabase.table("user_saved_cards").insert(payload).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to save card")

        row = response.data[0]
        return SavedCardResponse(
            id=row.get("id"),
            card_brand=row.get("card_brand", "card"),
            card_last_four=row.get("card_last_four", "0000"),
            card_exp_month=row.get("card_exp_month", 1),
            card_exp_year=row.get("card_exp_year", datetime.utcnow().year),
            cardholder_name=row.get("cardholder_name"),
            is_default=row.get("is_default", False),
            created_at=row.get("created_at"),
        )
    except Exception as e:
        logger.error(f"Error saving card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payment-history", response_model=UserPaymentHistoryResponse)
async def get_user_payment_history(current_user: dict = Depends(get_current_user)):
    """Get recent payment history for profile payment section."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")

        response = supabase.table("user_payment_history").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
        payments = response.data or []

        return UserPaymentHistoryResponse(payments=[
            UserPaymentRecordResponse(
                id=row.get("id"),
                amount_cents=int(row.get("amount_cents") or 0),
                currency=row.get("currency") or "usd",
                status=row.get("status") or "pending",
                transaction_type=row.get("transaction_type") or "payment",
                created_at=row.get("created_at"),
            )
            for row in payments
        ])
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscription/plans", response_model=SubscriptionPlansResponse)
async def get_subscription_plans(current_user: dict = Depends(get_current_user)):
    """Get available subscription plans shown in profile subscription subtab."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("pricing_plans").select("*").order("sort_order", desc=False).execute()
        rows = response.data or []

        if not rows:
            return SubscriptionPlansResponse(
                plans=[
                    SubscriptionPlanInfo(name="Free", price_display="$0", billing_period="mo", description="3 scans + translation", features=["basic_scan", "translation"]),
                    SubscriptionPlanInfo(name="Pro", price_display="$6.99", billing_period="mo", description="Unlimited + similar dishes + ingredients", features=["unlimited_scan", "similar_dishes", "ingredients"]),
                    SubscriptionPlanInfo(name="Max", price_display="$9.99", billing_period="mo", description="Pro + personalized recommendations", features=["unlimited_scan", "recommendations", "premium_support"]),
                ]
            )

        plans = []
        for row in rows:
            amount = row.get("amount_cents")
            if amount is not None:
                price_display = f"${(float(amount) / 100):.2f}"
            else:
                price_display = row.get("price_display") or "$0"

            plans.append(SubscriptionPlanInfo(
                name=row.get("name", "Free"),
                price_display=price_display,
                billing_period=row.get("billing_period", "mo"),
                description=row.get("description", ""),
                features=row.get("features") or [],
            ))

        return SubscriptionPlansResponse(plans=plans)
    except Exception as e:
        logger.error(f"Error getting subscription plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/subscription/select", response_model=UserSubscriptionInfo)
async def select_subscription_plan(
    selection: SelectSubscriptionPlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Select or switch a user's subscription plan."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        normalized_plan = selection.plan_name.strip().upper()

        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "plan_name": normalized_plan,
            "status": "active",
            "current_period_start": now.isoformat(),
            "current_period_end": (now + timedelta(days=30)).isoformat(),
            "cancel_at_period_end": False,
            "updated_at": now.isoformat(),
        }

        supabase.table("user_subscriptions").upsert(payload, {"on_conflict": "user_id"}).execute()
        return await get_subscription_info(current_user)
    except Exception as e:
        logger.error(f"Error selecting subscription plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's full profile including addresses and subscription."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get user profile
        user_response = supabase.table("users").select("*").eq("id", user_id).single().execute()
        
        # Get user addresses
        addresses_response = supabase.table("user_addresses").select("*").eq("user_id", user_id).execute()
        
        # Get user subscription
        subscription_response = supabase.table("user_subscriptions").select("""
            *,
            pricing_plans(name, description)
        """).eq("user_id", user_id).execute()
        
        return {
            "profile": user_response.data,
            "addresses": addresses_response.data,
            "subscription": subscription_response.data[0] if subscription_response.data else None
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile")
async def update_user_profile(
    profile: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile information."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Update user profile
        update_data = {k: v for k, v in profile.model_dump(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update profile")
            
        return {"message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/addresses", response_model=List[AddressResponse])
async def get_user_addresses(current_user: dict = Depends(get_current_user)):
    """Get user's addresses."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        response = supabase.table("user_addresses").select("*").eq("user_id", user_id).execute()
        
        return response.data
    except Exception as e:
        logger.error(f"Error getting user addresses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/addresses", response_model=AddressResponse)
async def create_address(
    address: AddressCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new address."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # If setting as primary, unset other primary addresses
        if address.is_primary:
            supabase.table("user_addresses").update({"is_primary": False}).eq("user_id", user_id).execute()
        
        address_data = {
            "user_id": user_id,
            "type": address.type,
            "street": address.street,
            "apartment_number": address.apartment_number,
            "city": address.city,
            "state": address.state,
            "zip_code": address.zip_code,
            "country": address.country,
            "is_primary": address.is_primary
        }
        
        response = supabase.table("user_addresses").insert(address_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create address")
            
        return response.data[0]
    except Exception as e:
        logger.error(f"Error creating address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str,
    address: AddressUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing address."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # If setting as primary, unset other primary addresses
        if address.is_primary:
            supabase.table("user_addresses").update({"is_primary": False}).eq("user_id", user_id).execute()
        
        update_data = {k: v for k, v in address.model_dump(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("user_addresses").update(update_data).eq("id", address_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Address not found")
            
        return response.data[0]
    except Exception as e:
        logger.error(f"Error updating address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an address."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        response = supabase.table("user_addresses").delete().eq("id", address_id).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Address not found")
            
        return {"message": "Address deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting address: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get current user to verify email
        user_response = supabase.table("users").select("email").eq("id", user_id).single().execute()
        user_email = user_response.data["email"]
        
        # Use Supabase Auth to change password
        auth_response = supabase.auth.update_user({
            "password": password_request.new_password
        })
        
        if auth_response.error:
            raise HTTPException(status_code=400, detail=auth_response.error.message)
        
        # Update password_changed_at timestamp
        supabase.table("users").update({
            "password_changed_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        
        return PasswordChangeResponse(
            message="Password changed successfully",
            password_changed_at=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription")
async def get_subscription_info(current_user: dict = Depends(get_current_user)):
    """Get user's subscription information."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get subscription with plan details when relation exists
        response = supabase.table("user_subscriptions").select("*,pricing_plans(name, description, features)").eq("user_id", user_id).limit(1).execute()
        
        if not response.data:
            # User doesn't have a subscription, return free plan
            return UserSubscriptionInfo(
                plan_name="Free",
                plan_description="Free plan with limited features",
                status="active",
                current_period_end=None,
                cancel_at_period_end=False
            )
        
        subscription = response.data[0]
        plan = subscription.get("pricing_plans") or {}

        plan_name = plan.get("name") or subscription.get("plan_name") or "Free"
        plan_description = plan.get("description") or f"{plan_name} plan"
        
        return UserSubscriptionInfo(
            plan_name=plan_name,
            plan_description=plan_description,
            status=subscription.get("status", "active"),
            current_period_end=subscription.get("current_period_end"),
            cancel_at_period_end=subscription.get("cancel_at_period_end", False)
        )
    except Exception as e:
        logger.error(f"Error getting subscription info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/referral", response_model=ReferralInfo)
async def get_referral_info(current_user: dict = Depends(get_current_user)):
    """Get user's referral information."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Get user profile with referral data
        user_response = supabase.table("users").select("referral_code, referral_count").eq("id", user_id).single().execute()
        user_data = user_response.data
        
        # Get referral history
        referrals_response = supabase.table("referrals").select("""
            *,
            referred_user:referee_id(full_name, email)
        """).eq("referrer_id", user_id).order("created_at", desc=True).execute()
        
        base_url = "https://menuocr.app"  # Update with your actual domain
        referral_link = f"{base_url}/signup?ref={user_data['referral_code']}"
        
        return ReferralInfo(
            referral_code=user_data["referral_code"],
            referral_count=user_data["referral_count"],
            referral_link=referral_link,
            pending_referrals=referrals_response.data
        )
    except Exception as e:
        logger.error(f"Error getting referral info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/referral/join")
async def join_with_referral(
    referral: ReferralCreate,
    current_user: dict = Depends(get_current_user)
):
    """Join using a referral code."""
    try:
        supabase = get_supabase_client()
        user_id = current_user.get("id")
        
        # Find referrer by referral code
        referrer_response = supabase.table("users").select("id").eq("referral_code", referral.referral_code).single().execute()
        
        if not referrer_response.data:
            raise HTTPException(status_code=400, detail="Invalid referral code")
        
        referrer_id = referrer_response.data["id"]
        
        # Check if user was already referred
        existing_referral = supabase.table("referrals").select("id").eq("referee_id", user_id).execute()
        
        if existing_referral.data:
            raise HTTPException(status_code=400, detail="You have already used a referral code")
        
        # Prevent self-referral
        if referrer_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot refer yourself")
        
        # Create referral record
        referral_data = {
            "referrer_id": referrer_id,
            "referee_id": user_id,
            "referral_code": referral.referral_code,
            "status": "completed",
            "reward_type": "subscription_months",
            "reward_amount": 1,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("referrals").insert(referral_data).execute()
        
        # Update referrer's referral count
        supabase.table("users").update({
            "referral_count": supabase.table("users").select("referral_count").eq("id", referrer_id).single().execute().data["referral_count"] + 1
        }).eq("id", referrer_id).execute()
        
        return {"message": "Referral code applied successfully! You and your referrer will receive benefits."}
    except Exception as e:
        logger.error(f"Error applying referral: {e}")
        raise HTTPException(status_code=500, detail=str(e))