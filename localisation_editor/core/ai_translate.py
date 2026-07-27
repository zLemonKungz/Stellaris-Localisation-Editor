"""
AI Translation module for the Localisation Editor.

Provides an AITranslator class that routes translation requests to
NVIDIA, Gemini, Claude, or Ollama based on user settings, with
consistent error handling and batch processing support.
"""

import re

from .settings_manager import SettingsManager

try:
    import requests
except ImportError:
    requests = None  # defer error reporting to call sites


class AITranslator:
    """Translates Stellaris game text into Thai using a configurable AI engine.

    Each provider (NVIDIA, Gemini, Claude, Ollama) is called through its
    REST API.  The engine is selected at call time via the *engine* parameter
    or via the ``default_engine`` setting.

    Usage::

        translator = AITranslator()
        result = translator.translate("Wormhole")
        # -> "รูโหมหนอนเวลา" (thai text)
    """

    _PROMPT_TEMPLATE = (
        "You are a translator for the game Stellaris (space 4X grand strategy).\n"
        "Translate the English text below into Thai.\n\n"
        "RULES:\n"
        "1. Understand the FULL meaning first, then rewrite in natural Thai."
        " Do NOT translate word-by-word.\n"
        "2. Use semi-formal game UI language — clear, concise, readable.\n"
        "3. Key terms: pop→ประชากร, empire→จักรวรรดิ, fleet→กองเรือ,"
        " planet→ดาวเคราะห์, resource→ทรัพยากร, technology→เทคโนโลยี,"
        " ship→ยาน, leader→ผู้นำ, trait→คุณลักษณะ, building→สิ่งปลูกสร้าง\n"
        "4. Keep $VARIABLE$, §R§G§Y§H§L...§! color codes, and £icon£ as-is.\n"
        "5. For proper names (ship names, planet names, species, events),"
        " transliterate or keep the original.\n"
        "6. Translate the meaning, not the words."
        " Make it sound like a real Thai game, not a dictionary.\n"
        "7. Output ONLY Thai text — no explanations, no notes.\n\n"
        "Example:\n"
        "  EN: 'This ancient empire once ruled the galaxy.'\n"
        "  TH: 'จักรวรรดิโบราณนี้เคยปกครองดาราจักร' (not: 'จักรวรรดิโบราณนี้ครั้งหนึ่งเคยปกครองทางช้างเผือก')\n\n"
        "{text}"
    )

    NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    NVIDIA_TIMEOUT = 120
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    CLAUDE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, settings: SettingsManager | None = None):
        """Initialise the translator.

        Args:
            settings: A SettingsManager instance.  If omitted a fresh
                      instance is created (loading ``config.json``).
        """
        self.settings = settings or SettingsManager()

    # ── Public API ───────────────────────────────────────────────────────

    def translate(self, text: str, engine: str | None = None) -> str:
        """Translate a single string of Stellaris English text to Thai.

        Args:
            text: The English text to translate.
            engine: One of ``"nvidia"``, ``"gemini"``, ``"claude"``,
                    ``"ollama"``.  Falls back to the ``default_engine``
                    setting when omitted.

        Returns:
            The translated Thai text, or an error string bracketed in
            ``[...]`` on failure.
        """
        if requests is None:
            return self._error("requests library not available")

        engine = (engine or self.settings.get("default_engine") or "ollama").lower()

        route = {
            "nvidia": self._translate_nvidia,
            "gemini": self._translate_gemini,
            "claude": self._translate_claude,
            "ollama": self._translate_ollama,
        }
        method = route.get(engine)
        if method is None:
            return f"[Error: Unknown engine '{engine}']"

        # Protect $VAR$, §color§!, £icon£ before sending to AI —
        # prevents the model from translating or mangling game syntax.
        protected_text, placeholders = self._protect_placeholders(text)
        result = method(protected_text)
        result = self._restore_placeholders(result, placeholders)
        return result

    def translate_batch(
        self,
        items: list[dict],
        engine: str | None = None,
        progress_callback: callable | None = None,
    ) -> list[dict]:
        """Translate a list of key-value items.

        Each item is a dict ``{"key": str, "value": str}``.  The method
        translates every ``"value"`` and adds a ``"translated"`` key to
        each item.

        Args:
            items: List of items to translate in place.
            engine: Translation engine to use.
            progress_callback: Optional ``callable(completed: int, total: int)``
                               invoked after each item.

        Returns:
            The same list with ``"translated"`` added to every item.
        """
        total = len(items)
        for i, item in enumerate(items):
            try:
                translated = self.translate(item.get("value", ""), engine=engine)
                item["translated"] = translated
            except Exception:
                item["translated"] = "[TRANSLATION FAILED]"
            if progress_callback:
                try:
                    progress_callback(i + 1, total)
                except Exception:
                    pass
        return items

    def test_connection(self, engine: str) -> str:
        """Test whether an engine is configured and reachable.

        Returns ``"OK"`` on success, or an error description on failure.
        """
        if requests is None:
            return "requests library not available"

        engine = engine.lower()
        testers = {
            "nvidia": self._test_nvidia,
            "gemini": self._test_gemini,
            "claude": self._test_claude,
            "ollama": self._test_ollama,
        }
        tester = testers.get(engine)
        if tester is None:
            return f"Unknown engine: {engine}"
        return tester()

    # ── NVIDIA ───────────────────────────────────────────────────────────

    def _translate_nvidia(self, text: str) -> str:
        api_key = self.settings.get("nvidia_api_key")
        if not api_key:
            return "[NVIDIA API: Missing or invalid API key]"

        model = self.settings.get("nvidia_model") or "meta/llama-3.1-8b-instruct"
        try:
            resp = requests.post(
                self.NVIDIA_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": self._build_prompt(text)}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2048,
                },
                timeout=self.NVIDIA_TIMEOUT,
            )
            if resp.status_code == 401:
                return "[NVIDIA API: Missing or invalid API key]"
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            return content.strip()
        except requests.exceptions.Timeout:
            return "[Error: NVIDIA API timed out]"
        except requests.exceptions.ConnectionError:
            return "[Error: Could not connect to NVIDIA API]"
        except Exception as exc:
            return self._error(str(exc))

    def _test_nvidia(self) -> str:
        api_key = self.settings.get("nvidia_api_key")
        if not api_key:
            return "Missing API key"

        # Check connectivity AND verify the configured model is available.
        try:
            resp = requests.get(
                "https://integrate.api.nvidia.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            if resp.status_code == 401:
                return "Invalid API key"
            if resp.status_code != 200:
                return f"Unexpected: HTTP {resp.status_code}"

            models = resp.json().get("data", [])
            model_ids = [m["id"] for m in models]
            configured = self.settings.get("nvidia_model") or "meta/llama-3.3-70b-instruct"

            if configured in model_ids:
                return f"OK (model '{configured}' is available)"
            else:
                available = ", ".join(model_ids[:8])
                return (
                    f"OK ({len(models)} models total), "
                    f"but '{configured}' NOT found. "
                    f"Available: {available}..."
                )
        except requests.exceptions.ConnectionError:
            return "Could not connect to NVIDIA API"
        except requests.exceptions.Timeout:
            return "Connection timed out"
        except Exception as exc:
            return str(exc)

    # ── Gemini ───────────────────────────────────────────────────────────

    def _translate_gemini(self, text: str) -> str:
        api_key = self.settings.get("gemini_api_key")
        if not api_key:
            return "[Gemini API: Missing API key]"

        model = self.settings.get("gemini_model") or "gemini-2.0-flash"
        url = f"{self.GEMINI_URL.format(model=model)}?key={api_key}"

        try:
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": self._build_prompt(text)}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 2048,
                    },
                },
                timeout=30,
            )

            # Handle structured error responses from Gemini
            if resp.status_code == 400:
                try:
                    err_data = resp.json()
                    msg = err_data.get("error", {}).get("message", "Bad request")
                    return self._error(f"Gemini API: {msg}")
                except Exception:
                    return "[Error: Gemini API returned 400]"
            if resp.status_code in (401, 403):
                return "[Gemini API: Missing API key]"

            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return "[Error: No response from Gemini]"

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return "[Error: Empty response from Gemini]"

            return parts[0].get("text", "").strip()
        except requests.exceptions.Timeout:
            return "[Error: Gemini API timed out]"
        except requests.exceptions.ConnectionError:
            return "[Error: Could not connect to Gemini API]"
        except Exception as exc:
            return self._error(str(exc))

    def _test_gemini(self) -> str:
        api_key = self.settings.get("gemini_api_key")
        if not api_key:
            return "Missing API key"

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = requests.get(url, timeout=10)
            if resp.status_code in (401, 403):
                return "Invalid API key"
            return "OK"
        except requests.exceptions.ConnectionError:
            return "Could not connect to Gemini API"
        except requests.exceptions.Timeout:
            return "Connection timed out"
        except Exception as exc:
            return str(exc)

    # ── Claude ───────────────────────────────────────────────────────────

    def _translate_claude(self, text: str) -> str:
        api_key = self.settings.get("claude_api_key")
        if not api_key:
            return "[Claude API: Missing API key]"

        model = self.settings.get("claude_model") or "claude-sonnet-5-20250721"

        try:
            resp = requests.post(
                self.CLAUDE_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 2048,
                    "temperature": 0.1,
                    "messages": [
                        {"role": "user", "content": self._build_prompt(text)}
                    ],
                },
                timeout=15,
            )
            if resp.status_code == 401:
                return "[Claude API: Missing API key]"
            resp.raise_for_status()
            data = resp.json()
            content_blocks = data.get("content", [])
            if not content_blocks:
                return "[Error: No response from Claude]"
            return content_blocks[0].get("text", "").strip()
        except requests.exceptions.Timeout:
            return "[Error: Claude API timed out]"
        except requests.exceptions.ConnectionError:
            return "[Error: Could not connect to Claude API]"
        except Exception as exc:
            return self._error(str(exc))

    def _test_claude(self) -> str:
        api_key = self.settings.get("claude_api_key")
        if not api_key:
            return "Missing API key"

        try:
            resp = requests.post(
                self.CLAUDE_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.get("claude_model") or "claude-sonnet-5-20250721",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
                timeout=10,
            )
            if resp.status_code == 401:
                return "Invalid API key"
            # Other non-2xx statuses (e.g. 400 for over-length) still
            # mean the endpoint is reachable and the key is valid.
            return "OK"
        except requests.exceptions.ConnectionError:
            return "Could not connect to Claude API"
        except requests.exceptions.Timeout:
            return "Connection timed out"
        except Exception as exc:
            return str(exc)

    # ── Ollama ───────────────────────────────────────────────────────────

    def _translate_ollama(self, text: str) -> str:
        endpoint = (self.settings.get("ollama_endpoint") or "http://localhost:11434").rstrip("/")
        model = self.settings.get("ollama_model") or "qwen2.5:7b"
        timeout = self.settings.get("ollama_timeout") or 60

        try:
            resp = requests.post(
                f"{endpoint}/api/generate",
                json={
                    "model": model,
                    "prompt": self._build_prompt(text),
                    "stream": False,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return "[Ollama: Not running]"
        except requests.exceptions.Timeout:
            return "[Error: Ollama timed out]"
        except Exception as exc:
            return self._error(str(exc))

    def _test_ollama(self) -> str:
        endpoint = (self.settings.get("ollama_endpoint") or "http://localhost:11434").rstrip("/")

        try:
            resp = requests.get(f"{endpoint}/api/tags", timeout=5)
            if resp.status_code == 200:
                return "OK"
            return f"Unexpected response: {resp.status_code}"
        except requests.exceptions.ConnectionError:
            return "Ollama: Not running"
        except requests.exceptions.Timeout:
            return "Connection timed out"
        except Exception as exc:
            return str(exc)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _build_prompt(self, text: str) -> str:
        """Return the full prompt string for the given text.

        Uses str.replace instead of str.format to avoid KeyError when
        the *text* itself contains curly braces (e.g. ``{0}``, ``{1}``),
        which are common in Stellaris localisation values.
        """
        return self._PROMPT_TEMPLATE.replace("{text}", text)

    # ── Placeholder protection ──────────────────────────────────────────────
    # Replace $VAR$, §color§!, £icon£ with safe tokens before sending the
    # text to an AI model, then restore them after translation.  This is the
    # only way to guarantee game syntax is never mangled.

    _PH_PREFIX = "__STELLARIS_PH_"
    _PH_PATTERN = re.compile(
        r'\$[A-Z_][A-Z0-9_.]*\$|'           # $KEY$ cross-references
        r'§[RGYHLrgyhl].*?§!|'              # §R..§! / §G..§! etc colour codes
        r'£[a-z_]+£'                         # £icon£ inline icons
    )

    def _protect_placeholders(self, text: str) -> tuple[str, list[str]]:
        """Replace all game-syntax tokens with __STELLARIS_PH_N__ placeholders.

        Returns (protected_text, original_placeholders) where the list
        preserves the original tokens in order so _restore_placeholders can
        put them back.
        """
        originals: list[str] = []

        def _replace(m):
            originals.append(m.group(0))
            return f"{self._PH_PREFIX}{len(originals) - 1}__"

        protected = self._PH_PATTERN.sub(_replace, text)
        return protected, originals

    def _restore_placeholders(self, text: str, originals: list[str]) -> str:
        """Put back the original $VAR$/§…§!/£icon£ tokens."""
        if not originals:
            return text

        def _restore(m):
            idx_str = m.group(1)
            try:
                idx = int(idx_str)
                if 0 <= idx < len(originals):
                    return originals[idx]
            except ValueError:
                pass
            return m.group(0)

        pattern = re.compile(re.escape(self._PH_PREFIX) + r"(\d+)__")
        return pattern.sub(_restore, text)

    @staticmethod
    def _error(message: str) -> str:
        """Wrap an error message in standard brackets."""
        return f"[Error: {message}]"
