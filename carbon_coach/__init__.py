"""Carbon Coach package.

A conversational agent built with Google ADK for Python that measures,
understands, and helps reduce personal and campus carbon footprints.
"""

import os

# Automatically load environment variables from .env if present
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k, _v = _k.strip(), _v.strip()
                    if _v:
                        os.environ[_k] = _v
    except Exception:
        pass

# Ensure only GOOGLE_API_KEY is active to prevent dual-key warnings
if "GOOGLE_API_KEY" in os.environ:
    os.environ.pop("GEMINI_API_KEY", None)

from . import agent

__all__ = ["agent"]
