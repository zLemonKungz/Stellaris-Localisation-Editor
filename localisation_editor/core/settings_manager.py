"""
Settings Manager for the Localisation Editor.
Stores application settings in localisation_editor/config.json.

Provides a simple key-value interface with defaults, auto-creating
the config file on first use.
"""

import json
from pathlib import Path

# Config directory is localisation_editor/ (one level up from core/)
CONFIG_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_SETTINGS = {
    "nvidia_api_key": "",
    "nvidia_model": "meta/llama-3.1-8b-instruct",
    "gemini_api_key": "",
    "gemini_model": "gemini-2.0-flash",
    "claude_api_key": "",
    "claude_model": "claude-sonnet-5-20250721",
    "ollama_endpoint": "http://localhost:11434",
    "ollama_model": "qwen2.5:7b",
    "default_engine": "ollama",
    "ollama_timeout": 60,
}


class SettingsManager:
    """Manages application settings stored in a JSON config file.

    Provides dict-like get/set access, persistent save/load, and
    automatic initialisation with defaults when the config file
    does not exist.

    Example:
        settings = SettingsManager()
        api_key = settings.get("nvidia_api_key")
        settings.set("default_engine", "gemini")
        settings.save()
    """

    def __init__(self, config_path: str | Path | None = None):
        """Initialise the settings manager.

        Args:
            config_path: Optional explicit path to the JSON config file.
                         Defaults to localisation_editor/config.json.
        """
        self._config_path: Path = Path(config_path) if config_path else CONFIG_PATH
        self._settings: dict = dict(DEFAULT_SETTINGS)
        self.load()

    # ── Public API ───────────────────────────────────────────────────────

    def get(self, key: str, default=None):
        """Return the value for *key*, or *default* if the key does not exist."""
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        """Set *key* to *value* (in-memory only; call save() to persist)."""
        self._settings[key] = value

    def save(self) -> None:
        """Write current settings to the JSON config file."""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as fh:
                json.dump(self._settings, fh, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as exc:
            raise RuntimeError(
                f"Cannot save settings to {self._config_path}: {exc}"
            ) from exc

    def load(self) -> None:
        """Load settings from the JSON config file.

        If the file does not exist, initialise with defaults and
        create the file.  Any keys present on disk override the
        defaults; new default keys are added automatically.
        """
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                # Merge: disk values take precedence, but any new defaults
                # that aren't on disk yet are preserved.
                self._settings = {**DEFAULT_SETTINGS, **data}
            except (json.JSONDecodeError, OSError):
                # Corrupted or unreadable -- fall back to defaults
                self._settings = dict(DEFAULT_SETTINGS)
                self.save()
        else:
            self._settings = dict(DEFAULT_SETTINGS)
            self.save()

    # ── Convenience accessors ────────────────────────────────────────────

    @property
    def all_settings(self) -> dict:
        """Return a copy of the full settings dict."""
        return dict(self._settings)

    @property
    def config_path(self) -> Path:
        """Return the path to the config file on disk."""
        return self._config_path
