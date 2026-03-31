"""
utils/cache.py
==============
In-memory query cache per user session.
PROFESSOR TEST POINT #7: same question → return stored response, don't call LLM again.

Cache key = hash of (username + customer_id + normalized_query)
Stored value = { "intent", "agent", "raw_result", "response" }
"""

import hashlib

# Global in-process cache: dict[cache_key → response_dict]
_cache: dict[str, dict] = {}

# Per-user cost/token running totals
_user_stats: dict[str, dict] = {}


def _make_key(username: str, customer_id: int, query: str) -> str:
    """Creates a deterministic cache key."""
    normalized = query.strip().lower()
    raw        = f"{username}:{customer_id}:{normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get(username: str, customer_id: int, query: str) -> dict | None:
    """Returns cached result or None on cache miss."""
    key = _make_key(username, customer_id, query)
    return _cache.get(key, None)


def set(username: str, customer_id: int, query: str, result: dict) -> str:
    """Stores result in cache. Returns the cache key (for logging)."""
    key = _make_key(username, customer_id, query)
    _cache[key] = result
    return key


def record_usage(username: str, tokens_in: int, tokens_out: int):
    """Accumulates token + cost usage per user."""
    if username not in _user_stats:
        _user_stats[username] = {
            "total_queries": 0,
            "cache_hits":    0,
            "tokens_in":     0,
            "tokens_out":    0,
            "est_cost_usd":  0.0,
        }
    s = _user_stats[username]
    s["total_queries"] += 1
    s["tokens_in"]     += tokens_in
    s["tokens_out"]    += tokens_out
    # GROQ LLaMA 3.3-70b rates
    s["est_cost_usd"]  += (tokens_in / 1_000_000) * 0.59 + (tokens_out / 1_000_000) * 0.79


def record_cache_hit(username: str):
    if username not in _user_stats:
        _user_stats[username] = {"total_queries": 0, "cache_hits": 0,
                                  "tokens_in": 0, "tokens_out": 0, "est_cost_usd": 0.0}
    _user_stats[username]["total_queries"] += 1
    _user_stats[username]["cache_hits"]    += 1


def get_all_user_stats() -> dict:
    """Returns usage stats for all users — used by admin dashboard."""
    return dict(_user_stats)


def get_user_stats(username: str) -> dict:
    return _user_stats.get(username, {
        "total_queries": 0, "cache_hits": 0,
        "tokens_in": 0, "tokens_out": 0, "est_cost_usd": 0.0,
    })


def clear_cache():
    """Clears all cached results (admin action)."""
    _cache.clear()


def cache_size() -> int:
    return len(_cache)
