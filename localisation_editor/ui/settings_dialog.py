"""
Settings dialog — configure AI translation providers for the
Stellaris Thai Translation MOD Localisation Editor.

Supports four AI backends:
  - NVIDIA AI Foundation API
  - Google Gemini API
  - Claude (Anthropic) API
  - Ollama (Local)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QComboBox,
    QApplication,
)

from .themes import DarkTheme


class SettingsDialog(QDialog):
    """Dialog for configuring AI translation provider settings."""

    TAB_NAMES = ["NVIDIA", "Google Gemini", "Claude (Anthropic)", "Ollama (Local)"]

    # Provider config: (engine_key, info_text, models list, has_endpoint)
    PROVIDER_CONFIG = [
        {
            "engine": "nvidia",
            "info": "NVIDIA AI Foundation API - 40 requests/min free. "
                    "Larger models = better translation but slower.",
            "models": [
                "meta/llama-3.3-70b-instruct",
                "meta/llama-3.1-70b-instruct",
                "meta/llama-3.1-8b-instruct",
                "mistralai/mixtral-8x22b-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct",
            ],
            "editable": True,
            "has_endpoint": False,
        },
        {
            "engine": "gemini",
            "info": "Gemini API - 60 requests/min free tier. "
                    "Pro models give better quality translations.",
            "models": [
                "gemini-2.0-flash",
                "gemini-2.0-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ],
            "editable": False,
            "has_endpoint": False,
        },
        {
            "engine": "claude",
            "info": "Claude API - requires API key from console.anthropic.com. "
                    "Opus is the most capable for nuanced translation.",
            "models": [
                "claude-sonnet-5-20250721",
                "claude-haiku-4.5-20251001",
                "claude-opus-5-20250721",
            ],
            "editable": False,
            "has_endpoint": False,
        },
        {
            "engine": "ollama",
            "info": "Local model - run ollama on your machine. "
                    "Larger models = better quality but need more RAM. "
                    "aya models are optimized for Thai.",
            "models": [
                "qwen2.5:7b",
                "qwen2.5:14b",
                "qwen2.5:32b",
                "gemma2:9b",
                "gemma2:27b",
                "aya-expanse:8b",
                "aya:35b",
                "llama3.3:70b",
            ],
            "editable": True,
            "has_endpoint": True,
        },
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        # Lazy import to avoid circular dependency
        from ..core.settings_manager import SettingsManager
        self._settings = SettingsManager()

        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 500)
        self.resize(550, 500)
        # Remove help button from title bar (PyQt6 compat)
        flags = self.windowFlags()
        try:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowContextHelpButtonHint)
        except AttributeError:
            pass

        self._api_key_inputs: dict[str, QLineEdit] = {}
        self._model_inputs: dict[str, QComboBox] = {}
        self._endpoint_inputs: dict[str, QLineEdit] = {}
        self._status_labels: dict[str, QLabel] = {}
        self._test_buttons: dict[str, QPushButton] = {}

        self._setup_ui()
        self._load_settings()

    # ── UI Setup ─────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel("⚙️ AI Translation Settings")
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        layout.addWidget(header)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        for cfg in self.PROVIDER_CONFIG:
            tab = self._build_provider_tab(cfg)
            self._tabs.addTab(tab, cfg["engine"].title())

        layout.addWidget(self._tabs, 1)

        # ── Bottom row: default engine + buttons ─────────────────────────
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        bottom_layout.addWidget(QLabel("Default engine:"))

        self._default_engine_combo = QComboBox()
        for cfg in self.PROVIDER_CONFIG:
            self._default_engine_combo.addItem(cfg["engine"])
        bottom_layout.addWidget(self._default_engine_combo)

        bottom_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold;
                padding: 8px 24px;
                border-radius: 4px;
            }}
        """)
        save_btn.clicked.connect(self._on_save)
        bottom_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_btn)

        layout.addLayout(bottom_layout)

    def _build_provider_tab(self, cfg: dict) -> QWidget:
        """Build one provider configuration tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(16, 16, 16, 16)

        # Info label
        info = QLabel(cfg["info"])
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            color: {DarkTheme.TEXT_SECONDARY.name()};
            font-size: 13px;
            padding: 8px 12px;
            background-color: {DarkTheme.BG_SURFACE.name()};
            border: 1px solid {DarkTheme.BORDER.name()};
            border-radius: 6px;
        """)
        tab_layout.addWidget(info)

        tab_layout.addSpacing(8)

        # API Key (or Endpoint) field
        if cfg["has_endpoint"]:
            endpoint_label = QLabel("Endpoint URL:")
            endpoint_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;")
            tab_layout.addWidget(endpoint_label)

            endpoint_input = QLineEdit()
            endpoint_input.setPlaceholderText("http://localhost:11434")
            endpoint_input.setText("http://localhost:11434")
            tab_layout.addWidget(endpoint_input)
            self._endpoint_inputs[cfg["engine"]] = endpoint_input

        key_label = QLabel("API Key:")
        key_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;")
        tab_layout.addWidget(key_label)

        key_input = QLineEdit()
        key_input.setEchoMode(QLineEdit.EchoMode.Password)
        key_input.setPlaceholderText("Enter your API key...")
        tab_layout.addWidget(key_input)
        self._api_key_inputs[cfg["engine"]] = key_input

        # Model selector
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;")
        tab_layout.addWidget(model_label)

        model_combo = QComboBox()
        model_combo.setEditable(cfg["editable"])
        for m in cfg["models"]:
            model_combo.addItem(m)
        tab_layout.addWidget(model_combo)
        self._model_inputs[cfg["engine"]] = model_combo

        tab_layout.addSpacing(12)

        # Test Connection button + status
        test_row = QHBoxLayout()
        test_row.setSpacing(8)

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(
            lambda checked=False, eng=cfg["engine"]: self._test_connection(eng)
        )
        test_row.addWidget(test_btn)
        self._test_buttons[cfg["engine"]] = test_btn

        # Disable test button unless API key is present (ollama always enabled)
        self._update_test_button_state(cfg["engine"])

        status_label = QLabel("")
        status_label.setWordWrap(True)
        self._status_labels[cfg["engine"]] = status_label
        test_row.addWidget(status_label, 1)

        tab_layout.addLayout(test_row)

        # React to API key changes so test button state stays current
        key_input.textChanged.connect(
            lambda text, eng=cfg["engine"]: self._update_test_button_state(eng)
        )

        tab_layout.addStretch()
        return tab

    # ── Settings Load / Save ─────────────────────────────────────────────

    def _update_test_button_state(self, engine: str):
        """Enable Test button only if API key is non-empty (ollama always enabled)."""
        btn = self._test_buttons.get(engine)
        if btn is None:
            return
        if engine == "ollama":
            btn.setEnabled(True)
        else:
            inp = self._api_key_inputs.get(engine)
            key_text = inp.text().strip() if inp else ""
            btn.setEnabled(bool(key_text))

    def _load_settings(self):
        """Load current settings into all fields."""
        for cfg in self.PROVIDER_CONFIG:
            eng = cfg["engine"]

            # API key
            key_val = self._settings.get(f"{eng}_api_key", "")
            if key_val:
                self._api_key_inputs[eng].setText(key_val)

            # Endpoint (ollama only)
            if cfg["has_endpoint"] and eng in self._endpoint_inputs:
                ep_val = self._settings.get(f"{eng}_endpoint", "http://localhost:11434")
                self._endpoint_inputs[eng].setText(ep_val)

            # Model
            model_val = self._settings.get(f"{eng}_model", "")
            if model_val:
                idx = self._model_inputs[eng].findText(model_val)
                if idx >= 0:
                    self._model_inputs[eng].setCurrentIndex(idx)
                else:
                    self._model_inputs[eng].setCurrentText(model_val)

        # Default engine
        default = self._settings.get("default_engine", "ollama")
        idx = self._default_engine_combo.findText(default)
        if idx >= 0:
            self._default_engine_combo.setCurrentIndex(idx)

    def _on_save(self):
        """Save all settings and close."""
        try:
            for cfg in self.PROVIDER_CONFIG:
                eng = cfg["engine"]
                api_key = self._api_key_inputs[eng].text().strip()
                self._settings.set(f"{eng}_api_key", api_key)

                model = self._model_inputs[eng].currentText().strip()
                self._settings.set(f"{eng}_model", model)

                if cfg["has_endpoint"] and eng in self._endpoint_inputs:
                    ep = self._endpoint_inputs[eng].text().strip()
                    if not ep:
                        ep = "http://localhost:11434"
                    self._settings.set(f"{eng}_endpoint", ep)

            self._settings.set(
                "default_engine", self._default_engine_combo.currentText().strip()
            )
            self._settings.save()
            self.accept()
        except Exception as exc:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save settings:\n{type(exc).__name__}: {exc}"
            )

    # ── Connection Testing ──────────────────────────────────────────────

    def _test_connection(self, engine: str):
        """
        Test the connection for a given engine.
        Import AITranslator lazily to avoid circular deps.
        """
        from ..core.ai_translate import AITranslator

        status_label = self._status_labels.get(engine)
        if not status_label:
            return

        status_label.setText("Testing...")
        status_label.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()};")
        QApplication.processEvents()

        try:
            translator = AITranslator(self._settings)
            result = translator.test_connection(engine)
            is_ok = result.strip().upper().startswith("OK")

            if is_ok:
                status_label.setText(f"✓ {result}")
                status_label.setStyleSheet(f"color: {DarkTheme.ACCENT_GREEN.name()};")
            else:
                status_label.setText(f"✗ {result}")
                status_label.setStyleSheet(f"color: {DarkTheme.ACCENT_RED.name()};")
        except Exception as exc:
            status_label.setText(f"✗ Error: {exc}")
            status_label.setStyleSheet(f"color: {DarkTheme.ACCENT_RED.name()};")
