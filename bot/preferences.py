from bot.clients import store
from bot.config import DEFAULT_PROVIDER, HF_SPACE_ID


def _is_valid_provider(provider: str) -> bool:
    """Read-time check: is this a provider we can actually serve right now?
    'hf' is only valid when HF_SPACE_ID is configured, so a stale 'hf'
    preference falls back to the default on read."""
    if not provider or not provider.strip():
        return False
    if provider == "hf":
        return bool(HF_SPACE_ID)
    if provider == "main":
        return True
    # Allow any explicit Cerebras model key if it is a real option.
    try:
        from bot.handlers import available_models

        return any(model["key"] == provider for model in available_models())
    except Exception:
        return False


def _is_writable_provider(provider: str) -> bool:
    """Write-time check: is this a key we recognise and are willing to persist?
    More permissive than the read check — 'hf' is accepted even when
    HF_SPACE_ID is currently unset, because get_provider() safely falls back
    to the default on read if HF stays unconfigured (stale-safe)."""
    if not provider or not provider.strip():
        return False
    if provider in ("main", "hf"):
        return True
    try:
        from bot.handlers import available_models

        return any(model["key"] == provider for model in available_models())
    except Exception:
        return False


def get_provider(user_id: int) -> str:
    """Return the user's chosen provider/model key, or DEFAULT_PROVIDER.

    Falls back to DEFAULT_PROVIDER if storage is not configured,
    storage is down, the user has no saved preference, or the saved
    preference is invalid or unavailable.
    """
    if store is None:
        return DEFAULT_PROVIDER
    try:
        value = store.get(f"provider:{user_id}")
    except Exception as e:
        print(f"Store read error (preferences): {e}")
        return DEFAULT_PROVIDER
    if not _is_valid_provider(value):
        return DEFAULT_PROVIDER
    return value


def set_provider(user_id: int, provider: str) -> bool:
    """Save the user's provider choice or explicit Cerebras model key."""
    if not _is_writable_provider(provider):
        return False
    if store is None:
        return False
    try:
        store.set(f"provider:{user_id}", provider)
        return True
    except Exception as e:
        print(f"Store write error (preferences): {e}")
        return False
