"""Global rate limiter and request budget tracker."""

import time
import random

_last_request_time = 0.0
_total_requests = 0


def rate_limit(min_interval: float = 1.0):
    """Enforce min interval + random 1-2s jitter between requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)
    time.sleep(random.uniform(1, 2))
    _last_request_time = time.time()


def track_request():
    """Increment the global request counter."""
    global _total_requests
    _total_requests += 1


def get_total_requests() -> int:
    """Return total requests spent in this session."""
    return _total_requests


def reset_budget():
    """Reset request counter to zero."""
    global _total_requests
    _total_requests = 0
