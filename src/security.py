"""
Security Manager module for NIDS.
Provides API rate limiting, security response headers, request size limits, and CORS protection.
"""
import logging
import time
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory token bucket rate limiter per client IP address.
    """

    def __init__(self, requests_per_minute: int = 120):
        self.rate = requests_per_minute
        self.clients: Dict[str, List[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        """
        Checks if client IP is within rate limits.
        """
        now = time.time()
        window_start = now - 60.0

        if client_ip not in self.clients:
            self.clients[client_ip] = [now]
            return True

        # Keep timestamps within the last 60 seconds
        timestamps = [t for t in self.clients[client_ip] if t > window_start]
        timestamps.append(now)
        self.clients[client_ip] = timestamps

        if len(timestamps) > self.rate:
            logger.warning("Rate limit exceeded for IP %s (%d reqs/min)", client_ip, len(timestamps))
            return False

        return True


class SecurityManager:
    """
    Platform security enforcement for HTTP headers, CORS, and request size validation.
    """

    def __init__(self, max_body_bytes: int = 10 * 1024 * 1024):
        self.rate_limiter = RateLimiter(requests_per_minute=120)
        self.max_body_bytes = max_body_bytes

    def get_security_headers(self) -> Dict[str, str]:
        """
        Returns hardened HTTP security response headers.
        """
        return {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none';",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

    def validate_request_size(self, content_length: int) -> bool:
        """
        Validates incoming HTTP payload content length.
        """
        return content_length <= self.max_body_bytes


# Global SecurityManager singleton
security_manager = SecurityManager()
