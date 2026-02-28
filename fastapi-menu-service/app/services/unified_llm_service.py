"""
Unified LLM Service - Supports multiple LLM providers
Supports: Kilocode, Ollama, OpenRouter, OpenAI, Anthropic
"""
import httpx
import json
from typing import Optional, Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class UnifiedLLMService:
    """Unified service for interacting with multiple LLM providers"""
    
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self._validate_provider()
        
    def _validate_provider(self):
        """Validate the configured provider"""
        valid_providers = ["kilocode", "ollama", "openrouter", "openai", "anthropic"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid LLM provider: {self.provider}. Valid options: {valid_providers}")
    
    def _get_kilocode_headers(self) -> Dict[str, str]:
        """Get headers for Kilocode API"""
        if not settings.kilocode_api_key:
            raise ValueError("KILOCODE_API_KEY is required for Kilocode provider")
        return {
            "Authorization": f"Bearer {settings.kilocode_api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_ollama_headers(self) -> Dict[str, str]:
        """Get headers for Ollama API (include ngrok-skip for ngrok free tier)"""
        headers = {"Content-Type": "application/json"}
        if settings.ollama_use_ngrok:
            headers["ngrok-skip-browser-warning"] = "true"
        return headers
    
    def _get_openrouter_headers(self) -> Dict[str, str]:
        """Get headers for OpenRouter API"""
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter provider")
        return {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Menu OCR App"
        }
    
    def _get_openai_headers(self) -> Dict[str, str]:
        """Get headers for OpenAI API"""
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        return {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
    
    def _get_anthropic_headers(self) -> Dict[str, str]:
        """Get headers for Anthropic API"""
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        return {
            "x-api-key": settings.anthropic_api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
    
    def _get_kilocode_url(self) -> str:
        """Get Kilocode API URL"""
        return f"{settings.kilocode_api_url}/chat/completions"
    
    def _get_ollama_url(self) -> str:
        """Get Ollama API URL (uses ngrok when OLLAMA_USE_NGROK=true)"""
        base_url = settings.get_ollama_base_url()
        return f"{base_url}/api/chat"
    
    def _get_openrouter_url(self) -> str:
        """Get OpenRouter API URL"""
        return "https://openrouter.ai/api/v1/chat/completions"
    
    def _get_openai_url(self) -> str:
        """Get OpenAI API URL"""
        return "https://api.openai.com/v1/chat/completions"
    
    def _get_anthropic_url(self) -> str:
        """Get Anthropic API URL"""
        return "https://api.anthropic.com/v1/messages"
    
    def _build_kilocode_payload(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build payload for Kilocode API"""
        payload = {
            "model": model or settings.kilocode_model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload
    
    def _build_ollama_payload(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build payload for Ollama API"""
        payload = {
            "model": model or settings.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        return payload
    
    def _build_openrouter_payload(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build payload for OpenRouter API"""
        payload = {
            "model": model or settings.llm_model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload
    
    def _build_openai_payload(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build payload for OpenAI API"""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload
    
    def _build_anthropic_payload(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Build payload for Anthropic API"""
        # Convert OpenAI format to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature
        }
        if system_message:
            payload["system"] = system_message
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return payload
    
    def _parse_kilocode_response(self, response: Dict[str, Any]) -> str:
        """Parse Kilocode API response"""
        return response["choices"][0]["message"]["content"]
    
    def _parse_ollama_response(self, response: Dict[str, Any]) -> str:
        """Parse Ollama API response"""
        return response["message"]["content"]
    
    def _parse_openrouter_response(self, response: Dict[str, Any]) -> str:
        """Parse OpenRouter API response"""
        return response["choices"][0]["message"]["content"]
    
    def _parse_openai_response(self, response: Dict[str, Any]) -> str:
        """Parse OpenAI API response"""
        return response["choices"][0]["message"]["content"]
    
    def _parse_anthropic_response(self, response: Dict[str, Any]) -> str:
        """Parse Anthropic API response"""
        return response["content"][0]["text"]
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 120.0
    ) -> str:
        """
        Send chat completion request to configured LLM provider
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Optional max tokens to generate
            timeout: Request timeout in seconds
            
        Returns:
            Generated text response
        """
        logger.info(f"Sending request to {self.provider} LLM provider")
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if self.provider == "kilocode":
                    url = self._get_kilocode_url()
                    headers = self._get_kilocode_headers()
                    payload = self._build_kilocode_payload(messages, model, temperature, max_tokens)
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return self._parse_kilocode_response(response.json())
                
                elif self.provider == "ollama":
                    url = self._get_ollama_url()
                    headers = self._get_ollama_headers()
                    payload = self._build_ollama_payload(messages, model, temperature, max_tokens)
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return self._parse_ollama_response(response.json())
                
                elif self.provider == "openrouter":
                    url = self._get_openrouter_url()
                    headers = self._get_openrouter_headers()
                    payload = self._build_openrouter_payload(messages, model, temperature, max_tokens)
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return self._parse_openrouter_response(response.json())
                
                elif self.provider == "openai":
                    url = self._get_openai_url()
                    headers = self._get_openai_headers()
                    payload = self._build_openai_payload(messages, model, temperature, max_tokens)
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return self._parse_openai_response(response.json())
                
                elif self.provider == "anthropic":
                    url = self._get_anthropic_url()
                    headers = self._get_anthropic_headers()
                    payload = self._build_anthropic_payload(messages, model, temperature, max_tokens)
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    return self._parse_anthropic_response(response.json())
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from {self.provider}: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error from {self.provider}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error from {self.provider}: {str(e)}")
            raise
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider configuration"""
        info = {
            "provider": self.provider,
            "configured": True
        }
        
        if self.provider == "kilocode":
            info.update({
                "model": settings.kilocode_model,
                "api_url": settings.kilocode_api_url,
                "api_key_configured": bool(settings.kilocode_api_key)
            })
        elif self.provider == "ollama":
            info.update({
                "model": settings.ollama_model,
                "api_url": settings.ollama_url
            })
        elif self.provider == "openrouter":
            info.update({
                "model": settings.llm_model,
                "api_key_configured": bool(settings.openrouter_api_key)
            })
        elif self.provider == "openai":
            info.update({
                "api_key_configured": bool(settings.openai_api_key)
            })
        elif self.provider == "anthropic":
            info.update({
                "api_key_configured": bool(settings.anthropic_api_key)
            })
        
        return info


# Global instance
llm_service = UnifiedLLMService()
