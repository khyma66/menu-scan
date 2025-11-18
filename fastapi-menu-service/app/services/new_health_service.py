"""New Health Recommendation Service - Complete rewrite with robust architecture."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


@dataclass
class HealthCondition:
    """Health condition data structure."""
    condition_type: str
    condition_name: str
    severity: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class HealthProfile:
    """Health profile data structure."""
    id: str
    user_id: str
    profile_name: Optional[str] = None
    is_active: bool = True
    conditions: List[HealthCondition] = None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []


@dataclass
class HealthRecommendation:
    """Health recommendation data structure."""
    menu_item: str
    recommendation_type: str  # 'safe', 'caution', 'avoid'
    reason: str
    confidence: float


class HealthValidationError(Exception):
    """Custom exception for health validation errors."""
    pass


class HealthServiceError(Exception):
    """Custom exception for health service errors."""
    pass


class HealthValidator:
    """Comprehensive input validation for health data."""

    VALID_CONDITION_TYPES = {'allergy', 'illness', 'dietary', 'preference'}
    VALID_SEVERITIES = {'mild', 'moderate', 'severe'}

    @staticmethod
    def validate_condition(condition: HealthCondition) -> None:
        """Validate a health condition."""
        if not condition.condition_type:
            raise HealthValidationError("Condition type is required")

        if condition.condition_type not in HealthValidator.VALID_CONDITION_TYPES:
            raise HealthValidationError(f"Invalid condition type: {condition.condition_type}")

        if not condition.condition_name or not condition.condition_name.strip():
            raise HealthValidationError("Condition name is required")

        if condition.severity and condition.severity not in HealthValidator.VALID_SEVERITIES:
            raise HealthValidationError(f"Invalid severity: {condition.severity}")

        # Sanitize inputs
        condition.condition_name = condition.condition_name.strip().lower()
        if condition.description:
            condition.description = condition.description.strip()

    @staticmethod
    def validate_profile_name(name: Optional[str]) -> Optional[str]:
        """Validate and sanitize profile name."""
        if name:
            name = name.strip()
            if len(name) > 100:
                raise HealthValidationError("Profile name too long (max 100 characters)")
            return name
        return None


class HealthProfileManager:
    """Manages health profiles with robust error handling."""

    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client

    async def create_profile(self, user_id: str, profile_name: Optional[str] = None) -> HealthProfile:
        """Create a new health profile for a user."""
        try:
            # Validate inputs
            validated_name = HealthValidator.validate_profile_name(profile_name)

            # Check if profile already exists
            existing = await self.get_profile(user_id)
            if existing:
                logger.info(f"Health profile already exists for user {user_id}")
                return existing

            # For now, just return a mock profile since we can't create new tables
            # In production, this would create a health_profiles record
            profile_id = f"profile_{user_id}"  # Mock ID
            logger.info(f"Created mock health profile {profile_id} for user {user_id}")

            return HealthProfile(
                id=profile_id,
                user_id=user_id,
                profile_name=validated_name,
                is_active=True
            )

        except Exception as e:
            logger.error(f"Error creating health profile for user {user_id}: {e}")
            raise HealthServiceError(f"Failed to create health profile: {str(e)}")

    async def get_profile(self, user_id: str) -> Optional[HealthProfile]:
        """Get health profile for a user."""
        try:
            # For now, return a mock profile and get conditions from health_conditions table
            profile_id = f"profile_{user_id}"

            # Get associated conditions from the existing health_conditions table
            conditions = await self._get_profile_conditions(user_id)

            return HealthProfile(
                id=profile_id,
                user_id=user_id,
                profile_name=None,
                is_active=True,
                conditions=conditions
            )

        except Exception as e:
            logger.error(f"Error getting health profile for user {user_id}: {e}")
            raise HealthServiceError(f"Failed to get health profile: {str(e)}")

    async def _get_profile_conditions(self, user_id: str) -> List[HealthCondition]:
        """Get all active conditions for a user from the existing health_conditions table."""
        try:
            response = self.supabase.client.table("health_conditions").select("*").eq("user_id", user_id).execute()

            conditions = []
            for cond_dict in response.data or []:
                conditions.append(HealthCondition(
                    condition_type=cond_dict['condition_type'],
                    condition_name=cond_dict['condition_name'],
                    severity=cond_dict.get('severity'),
                    description=cond_dict.get('description'),
                    metadata=None  # Existing table doesn't have metadata
                ))

            return conditions

        except Exception as e:
            logger.error(f"Error getting conditions for user {user_id}: {e}")
            return []


class HealthConditionManager:
    """Manages health conditions with comprehensive validation."""

    def __init__(self, supabase_client: SupabaseClient, profile_manager: HealthProfileManager):
        self.supabase = supabase_client
        self.profile_manager = profile_manager

    async def add_condition(self, user_id: str, condition: HealthCondition) -> str:
        """Add a health condition to user's profile."""
        try:
            # Validate condition
            HealthValidator.validate_condition(condition)

            # Check for duplicates in existing health_conditions table
            await self._check_duplicate_condition(user_id, condition)

            # Add condition to existing health_conditions table
            condition_data = {
                "user_id": user_id,
                "condition_type": condition.condition_type,
                "condition_name": condition.condition_name,
                "severity": condition.severity,
                "description": condition.description
            }

            response = self.supabase.client.table("health_conditions").insert(condition_data).execute()

            if not response.data:
                raise HealthServiceError("Failed to add health condition")

            condition_id = response.data[0]['id']
            logger.info(f"Added health condition {condition.condition_name} for user {user_id}")

            # Track analytics
            await self._track_analytics(user_id, 'add_condition', condition)

            return condition_id

        except HealthValidationError:
            raise
        except Exception as e:
            logger.error(f"Error adding condition for user {user_id}: {e}")
            raise HealthServiceError(f"Failed to add health condition: {str(e)}")

    async def remove_condition(self, user_id: str, condition_name: str) -> bool:
        """Remove a health condition from user's profile."""
        try:
            # Delete condition from existing health_conditions table
            response = self.supabase.client.table("health_conditions").delete().eq("user_id", user_id).eq("condition_name", condition_name).execute()

            success = len(response.data or []) > 0

            if success:
                logger.info(f"Removed health condition {condition_name} for user {user_id}")
                # Track analytics
                await self._track_analytics(user_id, 'remove_condition', HealthCondition(
                    condition_type='unknown',  # We don't have this info when removing
                    condition_name=condition_name
                ))

            return success

        except Exception as e:
            logger.error(f"Error removing condition {condition_name} for user {user_id}: {e}")
            raise HealthServiceError(f"Failed to remove health condition: {str(e)}")

    async def _check_duplicate_condition(self, user_id: str, condition: HealthCondition) -> None:
        """Check if condition already exists for user."""
        response = self.supabase.client.table("health_conditions").select("*").eq("user_id", user_id).eq("condition_name", condition.condition_name).execute()

        if response.data:
            raise HealthValidationError(f"Condition '{condition.condition_name}' already exists")

    async def _track_analytics(self, user_id: str, action: str, condition: HealthCondition) -> None:
        """Track health analytics."""
        try:
            analytics_data = {
                "user_id": user_id,
                "action": action,
                "condition_type": condition.condition_type,
                "condition_name": condition.condition_name,
                "metadata": {
                    "severity": condition.severity,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            self.supabase.client.table("health_analytics").insert(analytics_data).execute()

        except Exception as e:
            logger.warning(f"Failed to track analytics: {e}")


class HealthRecommendationEngine:
    """Generates health-based menu recommendations with caching."""

    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.cache_ttl_hours = 24

    async def get_recommendations(self, user_id: str, menu_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get health recommendations for menu items."""
        try:
            # Get user's health profile
            # Get user's health profile using the profile manager directly
            profile_manager = HealthProfileManager(self.supabase)
            profile = await profile_manager.get_profile(user_id)
            from app.services.new_health_service import HealthService
            health_service = HealthService()
            profile = await health_service.profile_manager.get_profile(user_id)

            if not profile or not profile.conditions:
                return self._empty_recommendations(menu_items)

            # Generate cache key
            conditions_hash = self._generate_conditions_hash(profile.conditions)

            # Check cache
            cached = await self._get_cached_recommendations(user_id, conditions_hash)
            if cached:
                logger.info(f"Using cached recommendations for user {user_id}")
                return cached

            # Generate new recommendations
            recommendations = await self._generate_recommendations(profile.conditions, menu_items)

            # Cache recommendations
            await self._cache_recommendations(user_id, conditions_hash, recommendations)

            # Track analytics
            await self._track_recommendation_analytics(user_id, len(menu_items), len(recommendations.get('recommendations', [])))

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            # Return safe fallback
            return self._empty_recommendations(menu_items)

    def _generate_conditions_hash(self, conditions: List[HealthCondition]) -> str:
        """Generate hash for conditions to use as cache key."""
        conditions_data = [
            {
                "type": c.condition_type,
                "name": c.condition_name,
                "severity": c.severity
            }
            for c in conditions
        ]
        conditions_json = json.dumps(conditions_data, sort_keys=True)
        return hashlib.sha256(conditions_json.encode()).hexdigest()

    async def _get_cached_recommendations(self, user_id: str, conditions_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached recommendations if still valid."""
        try:
            response = self.supabase.client.table("health_recommendations_cache").select("*").eq("user_id", user_id).eq("conditions_hash", conditions_hash).gt("expires_at", "now()").execute()

            if response.data:
                cache_entry = response.data[0]
                return cache_entry['recommendations']

        except Exception as e:
            logger.warning(f"Error checking cache: {e}")

        return None

    async def _cache_recommendations(self, user_id: str, conditions_hash: str, recommendations: Dict[str, Any]) -> None:
        """Cache recommendations."""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)

            cache_data = {
                "user_id": user_id,
                "conditions_hash": conditions_hash,
                "recommendations": recommendations,
                "expires_at": expires_at.isoformat()
            }

            # Upsert cache entry
            self.supabase.client.table("health_recommendations_cache").upsert(cache_data, {
                "on_conflict": "user_id,conditions_hash"
            }).execute()

        except Exception as e:
            logger.warning(f"Error caching recommendations: {e}")

    async def _generate_recommendations(self, conditions: List[HealthCondition], menu_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate recommendations based on conditions."""
        recommendations = []

        for item in menu_items:
            item_name = item.get('name', '').lower()
            item_description = item.get('description', '').lower()

            item_text = f"{item_name} {item_description}"

            # Check each condition
            for condition in conditions:
                recommendation = self._check_condition_against_item(condition, item_text)
                if recommendation:
                    recommendations.append({
                        "menu_item": item.get('name', ''),
                        "recommendation_type": recommendation['type'],
                        "reason": recommendation['reason'],
                        "condition": condition.condition_name,
                        "confidence": recommendation['confidence']
                    })
                    break  # Only one recommendation per item

        return {
            "recommendations": recommendations,
            "total_items": len(menu_items),
            "analyzed_conditions": len(conditions),
            "generated_at": datetime.utcnow().isoformat()
        }

    def _check_condition_against_item(self, condition: HealthCondition, item_text: str) -> Optional[Dict[str, Any]]:
        """Check if a condition affects a menu item."""
        # Simple keyword matching - in production, this would use ML/AI
        condition_keywords = self._get_condition_keywords(condition)

        for keyword in condition_keywords:
            if keyword.lower() in item_text:
                return {
                    "type": "avoid" if condition.condition_type == "allergy" else "caution",
                    "reason": f"Contains {condition.condition_name} ({condition.condition_type})",
                    "confidence": 0.8 if condition.severity == "severe" else 0.6
                }

        return None

    def _get_condition_keywords(self, condition: HealthCondition) -> List[str]:
        """Get keywords associated with a condition."""
        # This would typically come from a database table
        keyword_map = {
            "peanut": ["peanut", "groundnut"],
            "shellfish": ["shrimp", "crab", "lobster", "seafood"],
            "dairy": ["milk", "cheese", "butter", "cream"],
            "vegetarian": ["meat", "chicken", "beef", "pork", "fish"],
            "vegan": ["meat", "chicken", "beef", "pork", "fish", "egg", "dairy"],
            "fever": ["spicy", "heavy"],
            "nausea": ["fried", "spicy", "heavy"]
        }

        return keyword_map.get(condition.condition_name, [condition.condition_name])

    def _empty_recommendations(self, menu_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return empty recommendations structure."""
        return {
            "recommendations": [],
            "total_items": len(menu_items),
            "analyzed_conditions": 0,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _track_recommendation_analytics(self, user_id: str, total_items: int, recommendation_count: int) -> None:
        """Track recommendation analytics."""
        try:
            analytics_data = {
                "user_id": user_id,
                "action": "get_recommendations",
                "metadata": {
                    "total_items": total_items,
                    "recommendation_count": recommendation_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            self.supabase.client.table("health_analytics").insert(analytics_data).execute()

        except Exception as e:
            logger.warning(f"Failed to track recommendation analytics: {e}")


class HealthAnalytics:
    """Analytics and monitoring for health features."""

    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get health analytics for a user."""
        try:
            # Get condition counts by type
            response = self.supabase.client.table("health_analytics").select("*").eq("user_id", user_id).execute()

            stats = {
                "total_actions": len(response.data or []),
                "conditions_by_type": {},
                "recent_activity": []
            }

            for entry in response.data or []:
                action = entry.get('action')
                cond_type = entry.get('condition_type')

                if cond_type:
                    stats["conditions_by_type"][cond_type] = stats["conditions_by_type"].get(cond_type, 0) + 1

                if len(stats["recent_activity"]) < 10:
                    stats["recent_activity"].append({
                        "action": action,
                        "condition_name": entry.get('condition_name'),
                        "timestamp": entry.get('created_at')
                    })

            return stats

        except Exception as e:
            logger.error(f"Error getting analytics for user {user_id}: {e}")
            return {"error": str(e)}


class HealthService:
    """Main health service coordinating all components."""

    def __init__(self):
        self.supabase = SupabaseClient()
        self.profile_manager = HealthProfileManager(self.supabase)
        self.condition_manager = HealthConditionManager(self.supabase, self.profile_manager)
        self.recommendation_engine = HealthRecommendationEngine(self.supabase)
        self.analytics = HealthAnalytics(self.supabase)

    async def add_health_condition(self, user_id: str, condition: HealthCondition) -> str:
        """Add a health condition."""
        return await self.condition_manager.add_condition(user_id, condition)

    async def remove_health_condition(self, user_id: str, condition_name: str) -> bool:
        """Remove a health condition."""
        return await self.condition_manager.remove_condition(user_id, condition_name)

    async def get_health_recommendations(self, user_id: str, menu_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get health recommendations for menu items."""
        return await self.recommendation_engine.get_recommendations(user_id, menu_items)

    async def get_user_health_profile(self, user_id: str) -> Optional[HealthProfile]:
        """Get user's complete health profile."""
        return await self.profile_manager.get_profile(user_id)

    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user's health analytics."""
        return await self.analytics.get_user_stats(user_id)