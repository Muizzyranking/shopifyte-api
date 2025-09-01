from hashlib import md5
import json
from typing import Any, Optional
from django.conf import settings
from django.core.cache import cache as django_cache

from core.utils import get_seconds

DEFAULT_TIMEOUT = get_seconds(minutes=5)  # Default timeout in seconds


class Cache:

    def __init__(self, prefix: str = "cache", timeout: Optional[float] = None):
        if timeout is None or timeout <= 0 or not isinstance(timeout, float):
            timeout = getattr(settings, "CACHE_TIMEOUT", DEFAULT_TIMEOUT)
        self.timeout = timeout
        self.prefix = prefix
        self.cache = django_cache

    def _prefix_key(self, key: str) -> str:
        if not key.startswith(self.prefix):
            key = f"{self.prefix}:{key}"
        return key

    def generate_key(self, data: dict, suffix: str) -> str:
        try:
            sorted_data = json.dumps(data, sort_keys=True)
        except Exception:
            sorted_data = str(sorted(data.items()))
        hash = md5(sorted_data.encode()).hexdigest()
        if suffix:
            hash = f"{suffix}_{hash[:20]}"
        return self._prefix_key(hash)

    def get(self, key: str):
        try:
            key = self._prefix_key(key)
            cached_data = self.cache.get(key)
            return cached_data
        except Exception:
            print(f"Cant get cache for key: {key}")
            return None

    def set(self, key: str | dict, value: Any, timeout: Optional[float] = None):
        try:
            if isinstance(key, dict):
                key = self.generate_key(key)
            key = self._prefix_key(key)
            timeout = timeout or self.timeout
            return self.cache.set(key, value, timeout)
        except Exception:
            print(f"Cant set cache for key: {key}")
            return False

    def delete(self, key: str):
        try:
            key = self._prefix_key(key)
            return self.cache.delete(key)
        except Exception:
            print(f"Cant delete cache for key: {key}")
            return False

    def delete_pattern(self, pattern: str):
        try:
            pattern = self._prefix_key(pattern)
            if hasattr(self.cache, "delete_pattern"):
                return self.cache.delete_pattern(pattern)
            if hasattr(self.cache, "keys"):
                keys = self.cache.keys(pattern)
                if keys:
                    return self.cache.delete_many(keys)
            # clear all if pattern matching or not supported
            return self.cache.clear()
        except Exception:
            print(f"Cant delete cache for pattern or the pattern doesnt support: {pattern}")
            return False

    def clear(self):
        try:
            return self.delete_pattern("*")
        except Exception:
            print("Cant clear cache")
            return False
