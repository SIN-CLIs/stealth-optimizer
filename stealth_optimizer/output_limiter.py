import re
from typing import Optional

from stealth_config.config_manager import get_config


class OutputLimiter:
    def __init__(self, cfg=None):
        self.cfg = cfg or get_config()
        self.enabled = self.cfg.is_enabled("output_limiter")
        self.max_tokens = self.cfg.get("output_limiter", "max_tokens", {})
        self.trim_sentences = self.cfg.get("output_limiter", "trim_to_sentence", False)
        self._token_cache = {}

    def max_tokens_for(self, complexity: str) -> int:
        return self.max_tokens.get(complexity, 128)

    def estimate_tokens(self, text: str) -> int:
        return len(text.split())

    def trim(self, response: str, complexity: str) -> str:
        if not self.enabled:
            return response
        max_tok = self.max_tokens_for(complexity)
        tokens = response.split()
        if len(tokens) <= max_tok:
            return response
        if self.trim_sentences:
            truncated = " ".join(tokens[:max_tok])
            last_period = truncated.rfind(".")
            if last_period > max_tok * 0.5:
                return truncated[:last_period + 1]
        return " ".join(tokens[:max_tok]) + "…"

    def format_structured(self, response: str, fmt: str) -> str:
        if fmt == "json" and response:
            try:
                import json
                obj = json.loads(response)
                return json.dumps(obj, ensure_ascii=False)
            except Exception:
                pass
        return response

    def apply_to_llm_response(self, response: str, complexity: str) -> str:
        trimmed = self.trim(response, complexity)
        return trimmed


_limiter = None


def get_limiter() -> OutputLimiter:
    global _limiter
    if _limiter is None:
        _limiter = OutputLimiter()
    return _limiter


def limit(response: str, complexity: str = "mid") -> str:
    return get_limiter().apply_to_llm_response(response, complexity)