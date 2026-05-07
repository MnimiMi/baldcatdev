"""
Rate limiting configuration for Tarot API
Uses slowapi with flexible client identification (tg_id > session > IP)
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_identifier(request: Request) -> str:
    """
    Extract client identifier for rate limiting.
    Priority: tg_id (bot) > session_id (website) > IP (anonymous)
    """
    # Try TG ID from query params
    tg_id = request.query_params.get('tg_id') or \
            request.query_params.get('user_tg_id')

    # Try session ID from cookies or headers
    session_id = request.cookies.get('session_id') or \
                 request.headers.get('X-Session-ID') or \
                 request.cookies.get('PHPSESSID')

    if tg_id:
        return f"tg_{tg_id}"
    elif session_id:
        return f"sess_{session_id}"
    else:
        return f"ip_{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["100/minute"]
)
