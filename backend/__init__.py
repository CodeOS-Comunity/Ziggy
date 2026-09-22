"""Ziggy — the new and improved AI for CodeOS (Python backend)."""

__version__ = "1.0.0"

try:
    from . import engine  # noqa: F401
    from .engine import response  # noqa: F401
except ImportError:
    pass

__all__ = ["engine", "response", "__version__"]