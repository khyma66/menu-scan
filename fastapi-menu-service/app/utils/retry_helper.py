"""
Retry utility for handling transient failures with configurable retry logic.
"""
import asyncio
import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(
        self,
        enabled: bool = True,
        delay: int = 10,
        max_attempts: int = 3,
        backoff_multiplier: float = 1.0
    ):
        self.enabled = enabled
        self.delay = delay
        self.max_attempts = max_attempts
        self.backoff_multiplier = backoff_multiplier

# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig(enabled=True, delay=10, max_attempts=3)

async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: The async function to retry
        *args: Positional arguments for the function
        config: Retry configuration (uses default if None)
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    if not config.enabled:
        return await func(*args, **kwargs)
    
    last_exception = None
    current_delay = config.delay
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            logger.info(f"Attempting {func.__name__} (attempt {attempt}/{config.max_attempts})")
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"Successfully executed {func.__name__} on attempt {attempt}")
            return result
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {str(e)}"
            )
            
            if attempt < config.max_attempts:
                logger.info(f"Retrying in {current_delay} seconds...")
                await asyncio.sleep(current_delay)
                current_delay *= config.backoff_multiplier
            else:
                logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
    
    raise last_exception


def retry_sync(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Retry a synchronous function with exponential backoff.
    
    Args:
        func: The function to retry
        *args: Positional arguments for the function
        config: Retry configuration (uses default if None)
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    import time
    
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    if not config.enabled:
        return func(*args, **kwargs)
    
    last_exception = None
    current_delay = config.delay
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            logger.info(f"Attempting {func.__name__} (attempt {attempt}/{config.max_attempts})")
            result = func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"Successfully executed {func.__name__} on attempt {attempt}")
            return result
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {str(e)}"
            )
            
            if attempt < config.max_attempts:
                logger.info(f"Retrying in {current_delay} seconds...")
                time.sleep(current_delay)
                current_delay *= config.backoff_multiplier
            else:
                logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
    
    raise last_exception


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to async functions.
    
    Usage:
        @with_retry()
        async def my_function():
            # function code
            
        @with_retry(RetryConfig(max_attempts=5, delay=5))
        async def my_custom_retry_function():
            # function code
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


def with_retry_sync(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to synchronous functions.
    
    Usage:
        @with_retry_sync()
        def my_function():
            # function code
            
        @with_retry_sync(RetryConfig(max_attempts=5, delay=5))
        def my_custom_retry_function():
            # function code
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_sync(func, *args, config=config, **kwargs)
        return wrapper
    return decorator
