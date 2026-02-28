"""
LLM Provider Router - API endpoints for managing LLM provider selection
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.unified_llm_service import llm_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM Provider"])


class ProviderSwitchRequest(BaseModel):
    """Request model for switching LLM provider"""
    provider: str
    model: Optional[str] = None


class ProviderInfo(BaseModel):
    """Response model for provider information"""
    provider: str
    configured: bool
    model: Optional[str] = None
    api_url: Optional[str] = None
    api_key_configured: Optional[bool] = None


@router.get("/status", response_model=ProviderInfo)
async def get_provider_status():
    """
    Get current LLM provider status
    
    Returns information about the currently configured LLM provider
    """
    try:
        info = llm_service.get_provider_info()
        return ProviderInfo(**info)
    except Exception as e:
        logger.error(f"Error getting provider status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider status: {str(e)}"
        )


@router.get("/providers")
async def list_available_providers():
    """
    List all available LLM providers
    
    Returns a list of supported LLM providers with their configurations
    """
    providers = [
        {
            "id": "kilocode",
            "name": "Kilocode",
            "type": "cloud",
            "description": "Cloud-based LLM with qwen3-235b-a22b model",
            "default_model": "qwen3-235b-a22b",
            "requires_api_key": True,
            "api_key_env": "KILOCODE_API_KEY",
            "model_env": "KILOCODE_MODEL",
            "api_url_env": "KILOCODE_API_URL"
        },
        {
            "id": "ollama",
            "name": "Ollama",
            "type": "local",
            "description": "Local LLM with qwen3:32b model (100% privacy)",
            "default_model": "qwen3:32b",
            "requires_api_key": False,
            "model_env": "OLLAMA_MODEL",
            "api_url_env": "OLLAMA_URL"
        },
        {
            "id": "openrouter",
            "name": "OpenRouter",
            "type": "cloud",
            "description": "Cloud-based LLM with qwen-2.5-72b-instruct model",
            "default_model": "qwen/qwen-2.5-72b-instruct",
            "requires_api_key": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "model_env": "LLM_MODEL"
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "type": "cloud",
            "description": "Cloud-based LLM with GPT models",
            "default_model": "gpt-4",
            "requires_api_key": True,
            "api_key_env": "OPENAI_API_KEY"
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "type": "cloud",
            "description": "Cloud-based LLM with Claude models",
            "default_model": "claude-3-opus-20240229",
            "requires_api_key": True,
            "api_key_env": "ANTHROPIC_API_KEY"
        }
    ]
    
    return {
        "current_provider": settings.llm_provider,
        "providers": providers
    }


@router.post("/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """
    Switch LLM provider dynamically
    
    Note: This endpoint returns the configuration needed to switch providers.
    The actual switch requires updating the .env file and restarting the service.
    """
    valid_providers = ["kilocode", "ollama", "openrouter", "openai", "anthropic"]
    
    if request.provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Valid options: {', '.join(valid_providers)}"
        )
    
    # Get provider-specific configuration
    provider_config = {}
    
    if request.provider == "kilocode":
        provider_config = {
            "provider": "kilocode",
            "env_vars": {
                "LLM_PROVIDER": "kilocode",
                "KILOCODE_MODEL": request.model or "qwen3-235b-a22b",
                "KILOCODE_API_URL": "https://api.kilocode.ai/v1"
            },
            "required_env_vars": ["KILOCODE_API_KEY"],
            "optional_env_vars": ["KILOCODE_MODEL", "KILOCODE_API_URL"]
        }
    elif request.provider == "ollama":
        provider_config = {
            "provider": "ollama",
            "env_vars": {
                "LLM_PROVIDER": "ollama",
                "OLLAMA_URL": "http://localhost:11434",
                "OLLAMA_MODEL": request.model or "qwen3:32b"
            },
            "required_env_vars": [],
            "optional_env_vars": ["OLLAMA_URL", "OLLAMA_MODEL"]
        }
    elif request.provider == "openrouter":
        provider_config = {
            "provider": "openrouter",
            "env_vars": {
                "LLM_PROVIDER": "openrouter",
                "LLM_MODEL": request.model or "qwen/qwen-2.5-72b-instruct"
            },
            "required_env_vars": ["OPENROUTER_API_KEY"],
            "optional_env_vars": ["LLM_MODEL"]
        }
    elif request.provider == "openai":
        provider_config = {
            "provider": "openai",
            "env_vars": {
                "LLM_PROVIDER": "openai",
            },
            "required_env_vars": ["OPENAI_API_KEY"],
            "optional_env_vars": []
        }
    elif request.provider == "anthropic":
        provider_config = {
            "provider": "anthropic",
            "env_vars": {
                "LLM_PROVIDER": "anthropic",
            },
            "required_env_vars": ["ANTHROPIC_API_KEY"],
            "optional_env_vars": []
        }
    
    return {
        "message": f"To switch to {request.provider}, update your .env file with the following configuration and restart the service",
        "configuration": provider_config,
        "restart_required": True
    }


@router.get("/test")
async def test_current_provider():
    """
    Test the current LLM provider
    
    Sends a simple test request to verify the provider is working
    """
    try:
        test_messages = [
            {"role": "user", "content": "Say 'LLM provider is working' in exactly those words."}
        ]
        
        response = await llm_service.chat_completion(
            messages=test_messages,
            temperature=0.1,
            max_tokens=50,
            timeout=30.0
        )
        
        return {
            "success": True,
            "provider": settings.llm_provider,
            "response": response,
            "message": "LLM provider is working correctly"
        }
    except Exception as e:
        logger.error(f"LLM provider test failed: {str(e)}")
        return {
            "success": False,
            "provider": settings.llm_provider,
            "error": str(e),
            "message": "LLM provider test failed"
        }
