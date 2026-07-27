"""
AI Translate dialog — batch-translate English-only keys using one of
four AI backends (NVIDIA, Gemini, Claude, Ollama).

Scans all mod files for English-only entries, lets the user choose a
target file (or all files), then runs AI translation in a background
thread with real-time progress and a results table.
"""

import re

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QApplication, QFrame,
)
from PyQt6.QtGui import QColor, QBrush

from .themes import DarkTheme
from ..core.data_manager import DataManager, THAI_RE, is_pure_reference


# ── Colour helpers ─────────────────────────────────────────────────────────

_SUCCESS_BG = QColor("#1a3a2a")       # dark green for success rows
_FAILURE_BG = QColor("#3a1a1a")        # dark red for failure rows
_STATUS_GREEN = "#a6e3a1"
_STATUS_RED = "#f38ba8"
_STATUS_GRAY = "#6c7086"

# Rate limit delays per engine (ms between requests)
_RATE_LIMITS = {
    "nvidia": 2000,
    "gemini": 1200,
    "claude": 3000,
    "ollama": 500,
}


# ── Background Worker ─────────────────────────────────────────────────────

class TranslationWorker(QObject):
    """Processes translation requests in a background thread.

    Emits signals so the UI stays responsive throughout the batch.
    """

    progress = pyqtSignal(int, int, str)   # current, total, key_name
    result_ready = pyqtSignal(str, str, str, str, bool)  # fname, key, original, translated, success
    finished = pyqtSignal()

    def __init__(self, keys: list[tuple[str, str, str]],
                 translator, engine: str, delay_ms: int):
        super().__init__(None)
        self._keys = keys
        self._translator = translator
        self._engine = engine
        self._delay_s = delay_ms / 1000.0
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        import time

        for i, (fname, key, original) in enumerate(self._keys):
            if self._cancelled:
                break

            self.progress.emit(i + 1, len(self._keys), key)

            # Rate-limiting delay between requests
            if self._delay_s > 0 and i > 0:
                time.sleep(self._delay_s)

            translated = ""
            success = False
            try:
                translated = self._translator.translate(
                    original, engine=self._engine
                )
                success = bool(translated and translated.strip())
            except Exception:
                translated = ""
                success = False

            if not success:
                translated = translated or "[TRANSLATION FAILED]"

            self.result_ready.emit(fname, key, original, translated, success)

        self.finished.emit()


# ── Dialog ─────────────────────────────────────────────────────────────────

class AITranslateDialog(QDialog):
    """Dialog for batch AI translation of English-only keys."""

    # Regex to detect values that contain real English text (not just game syntax)
    _ENGLISH_TEXT_RE = re.compile(r"[A-Za-z]{3,}")

    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager

        # Lazy imports to avoid circular dependency
        from ..core.settings_manager import SettingsManager
        from ..core.ai_translate import AITranslator

        self._settings = SettingsManager()
        self._translator = AITranslator(self._settings)

        self.setWindowTitle("AI Translate")
        self.setMinimumSize(750, 600)
        self.resize(750, 600)
        # Remove help button (PyQt6 compat)
        try:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
            )
        except AttributeError:
            pass

        # Data
        self._english_only_keys: dict[str, list[tuple[str, str]]] = {}
        """{filename: [(key, value), ...]} — all English-only entries found."""

        self._results: list[dict] = []
        """Accumulated translation results: {filename, key, original, translated, success}."""

        self._translation_running = False
        self._total_keys = 0
        self._processed_keys = 0
        self._errors = 0

        # Background-thread state
        self._worker: TranslationWorker | None = None
        self._thread: QThread | None = None
        self._test_worker: QObject | None = None
        self._test_thread: QThread | None = None

        self._setup_ui()
        self._scan_files()

    # ── UI Setup ─────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Header ───────────────────────────────────────────────────────
        header = QLabel("🤖 AI Translate")
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        layout.addWidget(header)

        # ── Engine row ───────────────────────────────────────────────────
        engine_row = QHBoxLayout()
        engine_row.setSpacing(8)

        engine_row.addWidget(QLabel("Engine:"))

        self._engine_combo = QComboBox()
        for eng in ("ollama", "nvidia", "gemini", "claude"):
            self._engine_combo.addItem(eng)
        engine_row.addWidget(self._engine_combo)

        self._settings_btn = QPushButton("⚙️ Settings")
        self._settings_btn.clicked.connect(self._open_settings)
        engine_row.addWidget(self._settings_btn)

        # Status dot
        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet(f"color: {_STATUS_GRAY}; font-size: 18px;")
        self._status_dot.setToolTip("Connection status — unknown")
        engine_row.addWidget(self._status_dot)

        self._status_text = QLabel("Not tested")
        self._status_text.setStyleSheet(f"color: {_STATUS_GRAY}; font-size: 12px;")
        engine_row.addWidget(self._status_text)

        engine_row.addStretch()
        layout.addLayout(engine_row)

        # ── File selector ────────────────────────────────────────────────
        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        file_row.addWidget(QLabel("Target file:"))

        self._file_combo = QComboBox()
        self._file_combo.addItem("All files with English-only keys")
        file_row.addWidget(self._file_combo, 1)

        self._key_count_label = QLabel("")
        self._key_count_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 12px;"
        )
        file_row.addWidget(self._key_count_label)

        layout.addLayout(file_row)

        # ── Progress section ─────────────────────────────────────────────
        progress_group = QFrame()
        progress_group.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(4)
        progress_layout.setContentsMargins(12, 8, 12, 8)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        progress_layout.addWidget(self._progress_bar)

        progress_info_row = QHBoxLayout()
        self._progress_label = QLabel("0 / 0 keys")
        self._progress_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;"
        )
        progress_info_row.addWidget(self._progress_label)

        self._current_key_label = QLabel("")
        self._current_key_label.setStyleSheet(
            f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 12px;"
        )
        self._current_key_label.setTextFormat(Qt.TextFormat.PlainText)
        progress_info_row.addWidget(self._current_key_label, 1)

        progress_layout.addLayout(progress_info_row)
        layout.addWidget(progress_group)

        # ── Results table ────────────────────────────────────────────────
        table_label = QLabel("Results:")
        table_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_PRIMARY.name()};
            font-weight: bold;
            font-size: 13px;
        """)
        layout.addWidget(table_label)

        self._results_table = QTableWidget()
        self._results_table.setColumnCount(3)
        self._results_table.setHorizontalHeaderLabels(
            ["Key", "Original (EN)", "Translated (TH)"]
        )
        self._results_table.horizontalHeader().setStretchLastSection(True)
        self._results_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._results_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._results_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._results_table.setAlternatingRowColors(True)
        self._results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._results_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._results_table.verticalHeader().setVisible(False)
        layout.addWidget(self._results_table, 1)

        # ── Bottom buttons ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._start_btn = QPushButton("▶ Start Translate")
        self._start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT_GREEN.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #81c784;
            }}
            QPushButton:disabled {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                color: {DarkTheme.TEXT_MUTED.name()};
            }}
        """)
        self._start_btn.clicked.connect(self._start_translation)
        btn_row.addWidget(self._start_btn)

        self._cancel_btn = QPushButton("⏹ Cancel")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_translation)
        btn_row.addWidget(self._cancel_btn)

        btn_row.addStretch()

        self._apply_selected_btn = QPushButton("Apply Selected")
        self._apply_selected_btn.setEnabled(False)
        self._apply_selected_btn.clicked.connect(self._apply_selected)
        btn_row.addWidget(self._apply_selected_btn)

        self._apply_all_btn = QPushButton("Apply All")
        self._apply_all_btn.setEnabled(False)
        self._apply_all_btn.clicked.connect(self._apply_all)
        btn_row.addWidget(self._apply_all_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        # Wire engine change to status update
        self._engine_combo.currentTextChanged.connect(self._on_engine_changed)

    # ── File Scanning ────────────────────────────────────────────────────

    def _scan_files(self):
        """Scan all mod files for English-only keys and populate the file combo."""
        self._english_only_keys.clear()
        total_count = 0

        for fname in self.data_manager.file_names:
            yml = self.data_manager.get_file(fname)
            if not yml:
                continue

            file_english: list[tuple[str, str]] = []
            for entry in yml.entries:
                val = entry.value.strip()
                if not val:
                    continue
                # Skip entries with Thai text
                if THAI_RE.search(val):
                    continue
                # Skip pure-reference values (only game syntax)
                if is_pure_reference(val):
                    continue
                # Must contain real English text
                if not self._ENGLISH_TEXT_RE.search(val):
                    continue
                file_english.append((entry.key, val))

            if file_english:
                self._english_only_keys[fname] = file_english
                total_count += len(file_english)

        # Populate the file combo
        current_sel = self._file_combo.currentText()
        self._file_combo.clear()
        all_label = f"All files with English-only keys  ({total_count} keys)"
        self._file_combo.addItem(all_label)
        for fname in sorted(self._english_only_keys.keys()):
            cnt = len(self._english_only_keys[fname])
            self._file_combo.addItem(f"{fname}  ({cnt} keys)")

        # Restore selection if it was a real filename
        if current_sel:
            for i in range(self._file_combo.count()):
                if self._file_combo.itemText(i).startswith(
                    current_sel.split("  ")[0]
                ):
                    self._file_combo.setCurrentIndex(i)
                    break

        self._update_key_count()

    def _update_key_count(self):
        """Update the key count label based on the current file selection."""
        keys = self._get_selected_keys()
        self._key_count_label.setText(f"{len(keys)} keys to translate")
        self._progress_label.setText(f"0 / {len(keys)} keys")
        self._progress_bar.setValue(0)

    def _get_selected_keys(self) -> list[tuple[str, str, str]]:
        """
        Return list of (filename, key, value) for the currently selected
        file option.
        """
        text = self._file_combo.currentText()
        if text.startswith("All files"):
            result: list[tuple[str, str, str]] = []
            for fname, entries in sorted(self._english_only_keys.items()):
                for key, val in entries:
                    result.append((fname, key, val))
            return result

        # Extract filename from combo text:  "filename  (N keys)"
        filename = text.split("  ")[0]
        entries = self._english_only_keys.get(filename, [])
        return [(filename, key, val) for key, val in entries]

    # ── Engine / Status ──────────────────────────────────────────────────

    def _on_engine_changed(self, engine: str):
        """Update status indicator when the engine selection changes."""
        try:
            self._status_dot.setStyleSheet(f"color: {_STATUS_GRAY}; font-size: 18px;")
            self._status_text.setText("Not tested")
            self._status_text.setStyleSheet(f"color: {_STATUS_GRAY}; font-size: 12px;")
        except Exception:
            pass

    def _test_connection(self, engine: str):
        """Test the connection for the selected engine."""
        try:
            self._status_text.setText("Testing...")
            self._status_dot.setStyleSheet(f"color: {_STATUS_GRAY}; font-size: 18px;")
            QApplication.processEvents()

            result = self._translator.test_connection(engine)
            is_ok = result.strip().upper().startswith("OK")
            if is_ok:
                self._status_dot.setStyleSheet(
                    f"color: {_STATUS_GREEN}; font-size: 18px;"
                )
                self._status_text.setText("Connected")
                self._status_text.setStyleSheet(
                    f"color: {_STATUS_GREEN}; font-size: 12px;"
                )
            else:
                self._status_dot.setStyleSheet(
                    f"color: {_STATUS_RED}; font-size: 18px;"
                )
                self._status_text.setText(result)
                self._status_text.setStyleSheet(
                    f"color: {_STATUS_RED}; font-size: 12px;"
                )
        except Exception as exc:
            self._status_dot.setStyleSheet(
                f"color: {_STATUS_RED}; font-size: 18px;"
            )
            self._status_text.setText(str(exc))
            self._status_text.setStyleSheet(
                f"color: {_STATUS_RED}; font-size: 12px;"
            )

    def _test_connection_threaded(self, engine: str):
        """Test connection in a background thread so the UI doesn't freeze."""
        self._status_text.setText("Testing...")
        self._status_dot.setStyleSheet(f"color: {_STATUS_GRAY}; font-size: 18px;")
        QApplication.processEvents()

        # Clean up previous test thread if any
        self._cleanup_test_thread()

        # Run test in a one-shot thread
        class TestWorker(QObject):
            done = pyqtSignal(str)

            def __init__(self, translator, eng):
                super().__init__(None)
                self.translator = translator
                self.eng = eng

            def run(self):
                try:
                    result = self.translator.test_connection(self.eng)
                except Exception as exc:
                    result = str(exc)
                self.done.emit(result)

        self._test_worker = TestWorker(self._translator, engine)
        self._test_thread = QThread()
        self._test_worker.moveToThread(self._test_thread)

        def on_done(result):
            try:
                is_ok = result.strip().upper().startswith("OK")
                if is_ok:
                    self._status_dot.setStyleSheet(
                        f"color: {_STATUS_GREEN}; font-size: 18px;"
                    )
                    self._status_text.setText("Connected")
                    self._status_text.setStyleSheet(
                        f"color: {_STATUS_GREEN}; font-size: 12px;"
                    )
                else:
                    self._status_dot.setStyleSheet(
                        f"color: {_STATUS_RED}; font-size: 18px;"
                    )
                    self._status_text.setText(result)
                    self._status_text.setStyleSheet(
                        f"color: {_STATUS_RED}; font-size: 12px;"
                    )
            finally:
                self._cleanup_test_thread()

        self._test_worker.done.connect(on_done)
        self._test_thread.started.connect(self._test_worker.run)
        self._test_thread.start()

    def _cleanup_test_thread(self):
        """Safely clean up the test connection thread."""
        try:
            if self._test_thread and self._test_thread.isRunning():
                self._test_thread.quit()
                self._test_thread.wait(3000)
        except Exception:
            pass
        self._test_worker = None
        self._test_thread = None

    def _open_settings(self):
        """Open the Settings dialog."""
        try:
            from .settings_dialog import SettingsDialog
            dlg = SettingsDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                # Reload settings and translator
                from ..core.settings_manager import SettingsManager
                from ..core.ai_translate import AITranslator
                self._settings = SettingsManager()
                self._translator = AITranslator(self._settings)
                # Re-test connection (non-blocking)
                self._test_connection_threaded(self._engine_combo.currentText())
        except Exception as exc:
            QMessageBox.warning(
                self, "Settings Error",
                f"Error after saving settings:\n{type(exc).__name__}: {exc}"
            )

    # ── Translation ──────────────────────────────────────────────────────

    def _start_translation(self):
        """Run batch translation in a background thread."""
        try:
            if self._translation_running:
                return

            engine = self._engine_combo.currentText().strip()
            keys_to_translate = self._get_selected_keys()

            if not keys_to_translate:
                QMessageBox.information(
                    self, "No Keys",
                    "No English-only keys found to translate."
                )
                return

            # Pre-flight check: verify the engine is configured
            eng_key = re.sub(r'[^a-z]', '', engine.lower())
            needs_key = {"nvidia", "gemini", "claude"}
            if eng_key in needs_key:
                key_val = self._settings.get(f"{eng_key}_api_key", "").strip()
                if not key_val:
                    QMessageBox.warning(
                        self, "API Key Required",
                        f"No API key configured for {engine}.\n\n"
                        f"Go to Settings (⚙️ button) and enter your {engine.title()} API key first."
                    )
                    return

            # Reset state
            self._results.clear()
            self._results_table.setRowCount(0)
            self._translation_running = True
            self._errors = 0
            self._start_btn.setEnabled(False)
            self._cancel_btn.setEnabled(True)
            self._apply_selected_btn.setEnabled(False)
            self._apply_all_btn.setEnabled(False)

            self._total_keys = len(keys_to_translate)

            # Set up results table
            self._results_table.setRowCount(self._total_keys)

            # Rate limit delay
            eng_key = re.sub(r'[^a-z]', '', engine.lower())
            delay = _RATE_LIMITS.get(eng_key, 1500)

            # Create and start the background worker
            self._worker = TranslationWorker(
                list(keys_to_translate), self._translator, engine, delay
            )
            self._thread = QThread()
            self._worker.moveToThread(self._thread)

            # Wire signals
            self._worker.progress.connect(self._on_worker_progress)
            self._worker.result_ready.connect(self._on_worker_result)
            self._worker.finished.connect(self._on_worker_finished)

            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self._thread.quit)

            self._thread.start()
        except Exception:
            self._translation_running = False
            self._start_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)

    def _cancel_translation(self):
        """Cancel an in-progress translation."""
        try:
            if self._worker:
                self._worker.cancel()
        except Exception:
            pass

    # ── Worker signal handlers ──────────────────────────────────────────

    def _on_worker_progress(self, current: int, total: int, key_name: str):
        """Update UI from worker progress signal."""
        try:
            self._current_key_label.setText(f"Translating: {key_name}")
            pct = int((current / total) * 100) if total else 0
            self._progress_bar.setValue(pct)
            self._progress_label.setText(f"{current} / {total} keys")
        except Exception:
            pass

    def _on_worker_result(self, fname: str, key: str,
                          original: str, translated: str, success: bool):
        """Add one result to the table from worker result signal."""
        try:
            idx = len(self._results)
            if not success:
                self._errors += 1

            self._results.append({
                "filename": fname,
                "key": key,
                "original": original,
                "translated": translated,
                "success": success,
            })
            self._update_table_row(idx, key, original, translated, success)
        except Exception:
            pass

    def _on_worker_finished(self):
        """Called when the background worker has finished all keys."""
        try:
            self._processed_keys = self._total_keys
            self._progress_bar.setValue(100)
            self._progress_label.setText(
                f"{self._total_keys} / {self._total_keys} keys"
            )
            self._current_key_label.setText("")
            self._translation_running = False
            self._start_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)

            successful_count = sum(1 for r in self._results if r["success"])
            if successful_count > 0:
                self._apply_selected_btn.setEnabled(True)
                self._apply_all_btn.setEnabled(True)

            summary = (
                f"Translated {successful_count}/{self._total_keys} keys. "
                f"Errors: {self._errors}"
            )
            self._current_key_label.setText(summary)
            colour = (
                DarkTheme.ACCENT_GREEN.name() if self._errors == 0
                else DarkTheme.ACCENT_YELLOW.name()
            )
            self._current_key_label.setStyleSheet(
                f"color: {colour}; font-size: 13px; font-weight: bold;"
            )
        except Exception:
            pass
        finally:
            # Clean up thread — always runs even if body raised
            try:
                if self._thread:
                    self._thread.deleteLater()
                    self._thread = None
                if self._worker:
                    self._worker.deleteLater()
                    self._worker = None
            except Exception:
                pass

    def _update_table_row(
        self, row: int, key: str, original: str,
        translated: str, success: bool
    ):
        """Fill a single results-table row and colour it."""
        try:
            self._results_table.setItem(row, 0, QTableWidgetItem(key))
            self._results_table.setItem(row, 1, QTableWidgetItem(original))
            self._results_table.setItem(row, 2, QTableWidgetItem(translated))

            bg = _SUCCESS_BG if success else _FAILURE_BG
            for col in range(3):
                item = self._results_table.item(row, col)
                if item:
                    item.setBackground(QBrush(bg))
                    if not success:
                        item.setForeground(QBrush(DarkTheme.ACCENT_RED))
                    else:
                        item.setForeground(QBrush(DarkTheme.ACCENT_GREEN))
        except Exception:
            pass

    # ── Apply Translations ───────────────────────────────────────────────

    def _get_successful_results(self) -> list[dict]:
        """Return only results where translation succeeded."""
        return [r for r in self._results if r["success"]]

    def _apply_selected(self):
        """Apply only the currently selected rows in the table."""
        try:
            selected_rows = set()
            for item in self._results_table.selectedItems():
                selected_rows.add(item.row())

            if not selected_rows:
                QMessageBox.information(
                    self, "No Selection",
                    "Please select one or more rows in the results table."
                )
                return

            results_to_apply = [
                self._results[row] for row in selected_rows
                if row < len(self._results) and self._results[row]["success"]
            ]

            if not results_to_apply:
                QMessageBox.information(
                    self, "No Valid Rows",
                    "None of the selected rows contain successful translations."
                )
                return

            self._do_apply(results_to_apply)
        except Exception:
            pass

    def _apply_all(self):
        """Apply ALL successful translations."""
        try:
            results = self._get_successful_results()
            if not results:
                QMessageBox.information(
                    self, "No Translations",
                    "There are no successful translations to apply."
                )
                return
            self._do_apply(results)
        except Exception:
            pass

    def _do_apply(self, results: list[dict]):
        """Write a list of translation results to the mod files."""
        try:
            # Group by filename
            file_updates: dict[str, dict[str, str]] = {}
            for r in results:
                file_updates.setdefault(r["filename"], {})[r["key"]] = r["translated"]

            total_applied = 0
            for fname, updates in file_updates.items():
                yml = self.data_manager.get_file(fname)
                if yml is None:
                    continue
                count = yml.set_values(updates)
                if count > 0:
                    self.data_manager.save_file(fname)
                    total_applied += count

            # Update coverage caches
            self.data_manager.invalidate_coverage_cache()

            QMessageBox.information(
                self, "Apply Complete",
                f"Applied {total_applied} translation(s) across "
                f"{len(file_updates)} file(s)."
            )

            self._apply_selected_btn.setEnabled(False)
            self._apply_all_btn.setEnabled(False)
        except Exception:
            pass

    # ── Overrides ────────────────────────────────────────────────────────

    def closeEvent(self, event):
        """Confirm close if a translation is running, then clean up."""
        try:
            if self._translation_running:
                reply = QMessageBox.question(
                    self, "Translation in Progress",
                    "A translation is still running. Cancel and close?",
                    QMessageBox.StandardButton.Yes |
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return

            # Cancel worker if still running
            if self._worker:
                self._worker.cancel()

            # Clean up thread resources
            if self._thread and self._thread.isRunning():
                self._thread.quit()
                self._thread.wait(5000)
        except Exception:
            pass

        event.accept()
