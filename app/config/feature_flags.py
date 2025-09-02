"""
Feature Flags Framework for Python Backend
Lightweight runtime feature toggles for safe deployments
"""

import json
import os
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class FeatureFlag:
    key: str
    enabled: bool
    description: str
    environments: Optional[List[Environment]] = None
    rollout_percentage: int = 100
    metadata: Optional[Dict[str, Any]] = None


class FeatureFlagManager:
    """Centralized feature flag management for the backend"""
    
    def __init__(self):
        self.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        self.flags = self._load_flags()
        self.user_id: Optional[str] = None
    
    def _load_flags(self) -> Dict[str, FeatureFlag]:
        """Load feature flags from environment or defaults"""
        default_flags = {
            "enhanced_crawling": FeatureFlag(
                key="enhanced_crawling",
                enabled=True,
                description="Enable enhanced web crawling with AI classification",
                environments=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION],
                rollout_percentage=100,
            ),
            "ai_content_analysis": FeatureFlag(
                key="ai_content_analysis",
                enabled=False,
                description="Enable AI-powered content analysis and categorization",
                environments=[Environment.DEVELOPMENT, Environment.STAGING],
                rollout_percentage=25,
            ),
            "bulk_data_operations": FeatureFlag(
                key="bulk_data_operations",
                enabled=True,
                description="Enable bulk data import/export operations",
                environments=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION],
                rollout_percentage=100,
            ),
            "real_time_websockets": FeatureFlag(
                key="real_time_websockets",
                enabled=False,
                description="Enable real-time WebSocket connections for live updates",
                environments=[Environment.DEVELOPMENT],
                rollout_percentage=0,
            ),
            "advanced_search": FeatureFlag(
                key="advanced_search",
                enabled=True,
                description="Enable advanced search with filters and facets",
                environments=[Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION],
                rollout_percentage=100,
            ),
            "rate_limiting_v2": FeatureFlag(
                key="rate_limiting_v2",
                enabled=False,
                description="Enable new rate limiting algorithm",
                environments=[Environment.DEVELOPMENT, Environment.STAGING],
                rollout_percentage=10,
            ),
            "audit_logging_enhanced": FeatureFlag(
                key="audit_logging_enhanced",
                enabled=True,
                description="Enable enhanced audit logging with detailed tracking",
                environments=[Environment.STAGING, Environment.PRODUCTION],
                rollout_percentage=100,
            ),
        }
        
        try:
            # Try to load from environment variable
            env_flags = os.getenv("FEATURE_FLAGS")
            if env_flags:
                loaded_flags = json.loads(env_flags)
                for key, config in loaded_flags.items():
                    if key in default_flags:
                        flag = default_flags[key]
                        flag.enabled = config.get("enabled", flag.enabled)
                        flag.rollout_percentage = config.get("rollout_percentage", flag.rollout_percentage)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load feature flags from environment: {e}")
        
        return default_flags
    
    def is_enabled(self, flag_key: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature flag is enabled for the current context"""
        flag = self.flags.get(flag_key)
        if not flag:
            print(f"Warning: Feature flag '{flag_key}' not found")
            return False
        
        # Check environment restriction
        if flag.environments and self.environment not in flag.environments:
            return False
        
        # Check base enabled state
        if not flag.enabled:
            return False
        
        # Check rollout percentage
        if flag.rollout_percentage < 100:
            return self._is_in_rollout(flag_key, flag.rollout_percentage, user_id)
        
        return True
    
    def _is_in_rollout(self, flag_key: str, percentage: int, user_id: Optional[str] = None) -> bool:
        """Determine if user is in rollout percentage"""
        if percentage == 0:
            return False
        if percentage == 100:
            return True
        
        # Use deterministic hash based on flag key and user identifier
        identifier = user_id or self.user_id or "anonymous"
        hash_input = f"{flag_key}-{identifier}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
        return (hash_value % 100) < percentage
    
    def set_user_context(self, user_id: str) -> None:
        """Set user context for personalized rollouts"""
        self.user_id = user_id
    
    def get_all_flags(self) -> Dict[str, Dict[str, Any]]:
        """Get all feature flags (for admin/debug purposes)"""
        return {
            key: {
                "enabled": flag.enabled,
                "description": flag.description,
                "environments": [env.value for env in flag.environments] if flag.environments else None,
                "rollout_percentage": flag.rollout_percentage,
                "currently_enabled": self.is_enabled(key),
                "metadata": flag.metadata,
            }
            for key, flag in self.flags.items()
        }
    
    def override_flag(self, flag_key: str, enabled: bool) -> bool:
        """Override a feature flag (development only)"""
        if self.environment != Environment.DEVELOPMENT:
            print("Warning: Feature flag overrides only allowed in development")
            return False
        
        if flag_key in self.flags:
            self.flags[flag_key].enabled = enabled
            return True
        return False


# Global feature flag manager instance
feature_flags = FeatureFlagManager()


def is_feature_enabled(flag_key: str, user_id: Optional[str] = None) -> bool:
    """Convenience function to check if a feature is enabled"""
    return feature_flags.is_enabled(flag_key, user_id)


def feature_flag_required(flag_key: str, fallback_response: Any = None):
    """Decorator to require a feature flag for an endpoint"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not is_feature_enabled(flag_key):
                if fallback_response is not None:
                    return fallback_response
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=404,
                    detail=f"Feature '{flag_key}' is not available"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_feature_flag(flag_key: str, default_value: Any = None):
    """Context manager for feature flag gated code"""
    class FeatureFlagContext:
        def __init__(self, enabled: bool):
            self.enabled = enabled
        
        def __enter__(self):
            return self.enabled
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    
    return FeatureFlagContext(is_feature_enabled(flag_key))


# Example usage in FastAPI endpoints:
"""
from app.config.feature_flags import is_feature_enabled, feature_flag_required

@app.get("/api/v1/advanced-search")
@feature_flag_required("advanced_search")
async def advanced_search():
    # This endpoint only works if advanced_search flag is enabled
    pass

@app.get("/api/v1/data")
async def get_data():
    if is_feature_enabled("enhanced_crawling"):
        # Use enhanced crawling logic
        pass
    else:
        # Use standard crawling logic
        pass
"""
