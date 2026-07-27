"""
Main application window — coordinates all panels, menus, toolbar,
and keyboard shortcuts for the Localisation Editor.
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QFont
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar,
    QTabWidget, QLabel, QMessageBox, QApplication, QFileDialog,
    QDialog, QPushButton, QLineEdit, QTextEdit, QSizePolicy,
    QFrame, QStackedWidget,
)

from .themes import DarkTheme
from .file_browser import FileBrowser
from .data_grid import DataGrid
from .editor_panel import EditorPanel
from .dashboard import Dashboard
from .search_dialog import SearchPanel
from .glossary_panel import GlossaryPanel
from .key_analysis import KeyAnalysisPanel
from .import_dialog import ImportDialog
from ..core.data_manager import DataManager, THAI_RE, is_pure_reference
from ..core.spell_check import SpellChecker
from ..core.suggestion import SuggestionEngine
from ..core.settings_manager import SettingsManager
from ..core.ai_translate import AITranslator


class MainWindow(QMainWindow):
    """Main application window for the Stellaris Localisation Editor."""

    APP_NAME = "SLE"
    VERSION = "1.0.0"

    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        # Create spell checker and suggestion engine (builds from translations)
        self.spell_checker = SpellChecker(self.data_manager)
        self.suggestion_engine = SuggestionEngine(self.data_manager)
        self.settings_manager = SettingsManager()
        self.ai_translator = AITranslator(self.settings_manager)
        self._setup_window()
        self._create_menus()
        self._create_status_bar()
        self._create_central_widget()
        self._create_shortcuts()
        self._load_data()

    # ── Window setup ───────────────────────────────────────────────────

    def _setup_window(self):
        self._base_title = f"{self.APP_NAME} v{self.VERSION}"
        self.setWindowTitle(self._base_title)
        self.setMinimumSize(1200, 700)
        self.resize(1400, 850)

        # Apply dark theme
        self.setStyleSheet(DarkTheme.stylesheet())

        # Center on screen
        screen = QApplication.primaryScreen()
        if screen:
            center = screen.availableGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(center)
            self.move(frame.topLeft())

    def _update_window_title(self, filename: str = ""):
        """Update window title to show current file."""
        if filename:
            self.setWindowTitle(f"{filename} — {self._base_title}")
        else:
            self.setWindowTitle(self._base_title)

    # ── Menus ──────────────────────────────────────────────────────────

    def _create_menus(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")

        open_mod_action = QAction("📂 &Open Mod Folder...", self)
        open_mod_action.triggered.connect(self._open_mod_folder)
        file_menu.addAction(open_mod_action)

        file_menu.addSeparator()

        save_action = QAction("💾 &Save", self)
        save_action.triggered.connect(self._save_current_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        ai_translate_action = QAction("🤖 &AI Translate...", self)
        ai_translate_action.triggered.connect(self._show_ai_translate)
        file_menu.addAction(ai_translate_action)

        file_menu.addSeparator()

        package_action = QAction("📦 &Package for Translation...", self)
        package_action.triggered.connect(self._package_for_translation)
        file_menu.addAction(package_action)

        apply_action = QAction("📥 &Apply Translation Package...", self)
        apply_action.triggered.connect(self._apply_translation_package)
        file_menu.addAction(apply_action)

        file_menu.addSeparator()

        settings_action = QAction("⚙️ &Settings...", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit
        edit_menu = menubar.addMenu("&Edit")

        find_action = QAction("🔍 &Find in File...", self)
        find_action.triggered.connect(self._focus_search)
        edit_menu.addAction(find_action)

        global_search_action = QAction("🔍 &Global Search...", self)
        global_search_action.triggered.connect(
            lambda: self._main_tabs.setCurrentIndex(2)
        )
        edit_menu.addAction(global_search_action)

        edit_menu.addSeparator()

        batch_rename_action = QAction("✏️ &Batch Rename Key...", self)
        batch_rename_action.triggered.connect(self._batch_rename_dialog)
        edit_menu.addAction(batch_rename_action)

        # View
        view_menu = menubar.addMenu("&View")

        files_action = QAction("📁 &Editor", self)
        files_action.triggered.connect(
            lambda: self._main_tabs.setCurrentIndex(0)
        )
        view_menu.addAction(files_action)

        overview_action = QAction("📊 &Overview", self)
        overview_action.triggered.connect(
            lambda: self._main_tabs.setCurrentIndex(1)
        )
        view_menu.addAction(overview_action)

        search_action = QAction("🔍 &Search", self)
        search_action.triggered.connect(
            lambda: self._main_tabs.setCurrentIndex(2)
        )
        view_menu.addAction(search_action)

        view_menu.addSeparator()

        glossary_action = QAction("📖 &Glossary", self)
        glossary_action.triggered.connect(
            lambda: self._main_tabs.setCurrentIndex(3)
        )
        view_menu.addAction(glossary_action)

        keyanalysis_action = QAction("🏷️ &Key Analysis", self)
        keyanalysis_action.triggered.connect(
            lambda: self._main_tabs.setCurrentIndex(4)
        )
        view_menu.addAction(keyanalysis_action)

        # Help
        help_menu = menubar.addMenu("&Help")

        shortcuts_action = QAction("⌨️ &Keyboard Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ── Status Bar ─────────────────────────────────────────────────────

    def _create_status_bar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.status_label = QLabel("Ready")
        self.status.addWidget(self.status_label, 1)

        separator = QLabel("  |  ")
        separator.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()};")
        self.status.addPermanentWidget(separator)

        self.file_count_label = QLabel("📁 Files: --")
        self.status.addPermanentWidget(self.file_count_label)

        self.status.addPermanentWidget(QLabel("  "))

        self.coverage_status_label = QLabel("🎯 --")
        self.coverage_status_label.setStyleSheet(f"font-weight: bold;")
        self.status.addPermanentWidget(self.coverage_status_label)

        self.status.addPermanentWidget(QLabel("  "))

        self.old_coverage_label = QLabel("")
        self.old_coverage_label.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 11px;")
        self.status.addPermanentWidget(self.old_coverage_label)

        self.status.addPermanentWidget(QLabel("  "))

        self.modified_label = QLabel("")
        self.status.addPermanentWidget(self.modified_label)

    # ── Central Widget ─────────────────────────────────────────────────

    def _create_central_widget(self):
        """Create the main layout with 5 consolidated tabs."""
        self._main_tabs = QTabWidget()
        self._main_tabs.setDocumentMode(True)
        self._main_tabs.currentChanged.connect(self._on_tab_changed)

        # ═══════════════════════════════════════════════════════════════
        # Tab 0: 📁 Editor — File browser + Data grid + Editor
        # ═══════════════════════════════════════════════════════════════
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        editor_layout.setContentsMargins(3, 3, 3, 3)
        editor_layout.setSpacing(3)

        # Stacked widget: page 0 = welcome, page 1 = normal editor
        self.editor_stack = QStackedWidget()

        # Page 0: welcome / empty state — a clean landing page
        self.welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.setSpacing(8)

        # App name
        name_label = QLabel("SLE")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            font-size: 42px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        welcome_layout.addWidget(name_label)

        # Subtitle
        sub_label = QLabel("Stellaris Localisation Editor")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet(f"""
            font-size: 16px; font-weight: normal;
            color: {DarkTheme.TEXT_SECONDARY.name()};
            margin-bottom: 20px;
        """)
        welcome_layout.addWidget(sub_label)

        # Separator line
        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.Shape.HLine)
        sep_line.setFixedWidth(300)
        sep_line.setStyleSheet(f"color: {DarkTheme.BORDER.name()};")
        sep_line.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        welcome_layout.addWidget(sep_line, 0, Qt.AlignmentFlag.AlignCenter)

        # Quick start card
        quick_card = QFrame()
        quick_card.setObjectName("welcome_card")
        quick_card.setFixedWidth(420)
        quick_card.setStyleSheet(f"""
            QFrame#welcome_card {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 10px;
                padding: 16px 20px;
            }}
        """)
        card_layout = QVBoxLayout(quick_card)
        card_layout.setSpacing(10)

        title1 = QLabel("Quick Start")
        title1.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {DarkTheme.TEXT_PRIMARY.name()};")
        card_layout.addWidget(title1)

        help1 = QLabel("1. Open a Stellaris mod folder to start translating")
        help1.setWordWrap(True)
        help1.setStyleSheet(f"font-size: 13px; color: {DarkTheme.TEXT_SECONDARY.name()};")
        card_layout.addWidget(help1)

        help2 = QLabel("2. Browse files in the left panel, edit values in the table")
        help2.setWordWrap(True)
        help2.setStyleSheet(f"font-size: 13px; color: {DarkTheme.TEXT_SECONDARY.name()};")
        card_layout.addWidget(help2)

        help3 = QLabel("3. Use AI Translate or edit manually, then save")
        help3.setWordWrap(True)
        help3.setStyleSheet(f"font-size: 13px; color: {DarkTheme.TEXT_SECONDARY.name()};")
        card_layout.addWidget(help3)

        welcome_layout.addWidget(quick_card, 0, Qt.AlignmentFlag.AlignCenter)
        self.editor_stack.addWidget(self.welcome_widget)  # index 0

        # Page 1: normal editor content
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: file browser
        self.file_browser = FileBrowser(self.data_manager)
        self.file_browser.file_selected.connect(self._on_file_selected)
        self.file_browser.file_double_clicked.connect(self._open_file)
        self.file_browser.setMinimumWidth(200)
        self.file_browser.setMaximumWidth(350)
        main_splitter.addWidget(self.file_browser)

        # Right: data grid (top) + editor panel (bottom)
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        self.data_grid = DataGrid(self.data_manager)
        self.data_grid.value_changed.connect(self._on_value_changed)
        self.data_grid.file_opened.connect(self._update_window_title)
        right_splitter.addWidget(self.data_grid)

        self.editor_panel = EditorPanel(
            spell_checker=self.spell_checker,
            suggestion_engine=self.suggestion_engine,
        )
        self.editor_panel.value_saved.connect(self._on_editor_saved)
        self.editor_panel.navigate_prev.connect(self._editor_prev_untranslated)
        self.editor_panel.navigate_next.connect(self._editor_next_untranslated)
        right_splitter.addWidget(self.editor_panel)

        right_splitter.setSizes([550, 180])

        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([220, 750])

        self.editor_stack.addWidget(main_splitter)  # index 1

        editor_layout.addWidget(self.editor_stack, 1)

        self._main_tabs.addTab(editor_tab, "📁 Editor")

        # ═══════════════════════════════════════════════════════════════
        # Tab 1: 📊 Overview — Dashboard with REAL quality stats
        # ═══════════════════════════════════════════════════════════════
        self.dashboard = Dashboard(self.data_manager)
        self.dashboard.navigate_to.connect(self._navigate_to_result)
        self._main_tabs.addTab(self.dashboard, "📊 Overview")

        # ═══════════════════════════════════════════════════════════════
        # Tab 2: 🔍 Search — Global search (unchanged)
        # ═══════════════════════════════════════════════════════════════
        self.search_panel = SearchPanel(self.data_manager)
        self.search_panel.navigate_to.connect(self._navigate_to_result)
        self._main_tabs.addTab(self.search_panel, "🔍 Search")

        # ═══════════════════════════════════════════════════════════════
        # Tab 3: 📖 Glossary
        # ═══════════════════════════════════════════════════════════════
        self.glossary_panel = GlossaryPanel(self.data_manager)
        self._main_tabs.addTab(self.glossary_panel, "📖 Glossary")

        # ═══════════════════════════════════════════════════════════════
        # Tab 4: 🏷️ Key Analysis
        # ═══════════════════════════════════════════════════════════════
        self.key_analysis = KeyAnalysisPanel(self.data_manager)
        self.key_analysis.navigate_to.connect(self._navigate_to_result)
        self._main_tabs.addTab(self.key_analysis, "🏷️ Key Analysis")

        self.setCentralWidget(self._main_tabs)

    # ── Keyboard shortcuts ─────────────────────────────────────────────

    def _create_shortcuts(self):
        # Ctrl+E - focus the editor panel
        focus_editor = QAction("Focus Editor", self)
        focus_editor.setShortcut(QKeySequence("Ctrl+E"))
        focus_editor.triggered.connect(
            lambda: self._editor_focus()
        )
        self.addAction(focus_editor)

        # Ctrl+Return - save current value
        save_value = QAction("Save Value", self)
        save_value.setShortcut(QKeySequence("Ctrl+Return"))
        save_value.triggered.connect(
            self.editor_panel._save_value
        )
        self.addAction(save_value)

    def _editor_focus(self):
        """Focus the editor panel text widget."""
        try:
            self.editor_panel.editor.setFocus()
            self.status_label.setText("Editor focused")
        except Exception as exc:
            self.status_label.setText(f"Error: {exc}")

    # ── Data Loading ───────────────────────────────────────────────────

    def _load_data(self):
        """Initial data load. Skips if no mod folder is opened."""
        if not self.data_manager.has_mod_folder:
            self.editor_stack.setCurrentIndex(0)  # show welcome
            self.status_label.setText(
                "No mod folder opened — use File > Open Mod Folder... (Ctrl+O)"
            )
            self.file_count_label.setText("📁 Files: --")
            self.coverage_status_label.setText("🎯 --")
            self.old_coverage_label.setText("")
            self.modified_label.setText("")
            return

        self.status_label.setText("Loading translation files...")
        QApplication.processEvents()

        try:
            self.editor_stack.setCurrentIndex(1)  # show editor
            self.file_browser.refresh()
            stats = self.data_manager.get_overall_stats()
            real_stats = self.data_manager.get_real_overall_stats()
            self._update_status_bar(stats, real_stats)

            # Load consolidated tab panels
            self.dashboard.refresh()
            self.glossary_panel.refresh()
            self.key_analysis.refresh()

            self.status_label.setText(
                f"Loaded {stats['total_files']} files, "
                f"{stats['total_keys']:,} keys total"
            )
        except Exception as exc:
            self.status_label.setText(f"Error loading data: {exc}")

    # ── Event Handlers ─────────────────────────────────────────────────

    def _on_file_selected(self, filename: str):
        """Called when a file is selected in the browser (single click)."""
        pass

    def _open_file(self, filename: str):
        """Open a file in the data grid. Auto-saves current file first."""
        try:
            # Auto-save current file before switching
            current = self.data_grid.current_file
            if current and current != filename and self.data_grid.save_btn.isEnabled():
                self.data_grid._save_current_file()
                self.file_browser.update_item(current)
            self.data_grid.open_file(filename)
            self._update_window_title(filename)
            self.status_label.setText(f"Editing: {filename}")
            self._main_tabs.setCurrentIndex(0)
        except Exception as exc:
            QMessageBox.critical(self, "Error Opening File",
                                 f"Failed to open {filename}:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    def _on_value_changed(self, key: str, value: str):
        """Called when a value is selected/changed in the data grid."""
        try:
            if self.data_grid.current_file:
                self.editor_panel.set_value(
                    key, value, self.data_grid.current_file
                )
        except Exception as exc:
            self.status_label.setText(f"Error loading value: {exc}")

    def _on_editor_saved(self, key: str, value: str):
        """Called when the editor panel saves a value."""
        try:
            self.data_grid.update_value(key, value)
            if self.data_grid.current_file:
                yml = self.data_manager.get_file(
                    self.data_grid.current_file
                )
                if yml:
                    yml.set_values({key: value})
                    self.data_manager.save_file(
                        self.data_grid.current_file
                    )
                    # Update coverage displays
                    self.file_browser.update_item(
                        self.data_grid.current_file
                    )
                    stats = self.data_manager.get_overall_stats()
                    real = self.data_manager.get_real_overall_stats()
                    self._update_status_bar(stats, real)
            self.status_label.setText(f"✓ Saved: {key}")
        except Exception as exc:
            QMessageBox.critical(self, "Error Saving",
                                 f"Failed to save value:\n{exc}")
            self.status_label.setText(f"Error saving: {exc}")

    def _navigate_to_result(self, filename: str, key: str):
        """Navigate to a search result."""
        try:
            self._main_tabs.setCurrentIndex(0)
            self._open_file(filename)
            self.status_label.setText(f"Navigated to: {key}")
        except Exception as exc:
            self.status_label.setText(f"Error navigating: {exc}")

    def _editor_prev_untranslated(self):
        """Navigate to the previous untranslated key in the current file."""
        try:
            filename = self.data_grid.current_file
            if not filename:
                return
            yml = self.data_manager.get_file(filename)
            if not yml:
                return
            current_key = self.editor_panel._current_key
            current_idx = -1
            for i, e in enumerate(yml.entries):
                if e.key == current_key:
                    current_idx = i
                    break
            n = len(yml.entries)
            for offset in range(1, n):
                idx = (current_idx - offset) % n
                if not yml.entries[idx].value.strip():
                    self._select_key_in_grid(filename, yml.entries[idx].key)
                    self.status_label.setText(f"Previous untranslated: {yml.entries[idx].key}")
                    return
            self.status_label.setText("No previous untranslated key found")
        except Exception as exc:
            self.status_label.setText(f"Error: {exc}")

    def _editor_next_untranslated(self):
        """Navigate to the next untranslated key in the current file."""
        try:
            filename = self.data_grid.current_file
            if not filename:
                return
            yml = self.data_manager.get_file(filename)
            if not yml:
                return
            current_key = self.editor_panel._current_key
            current_idx = -1
            for i, e in enumerate(yml.entries):
                if e.key == current_key:
                    current_idx = i
                    break
            n = len(yml.entries)
            for offset in range(1, n):
                idx = (current_idx + offset) % n
                if not yml.entries[idx].value.strip():
                    self._select_key_in_grid(filename, yml.entries[idx].key)
                    self.status_label.setText(f"Next untranslated: {yml.entries[idx].key}")
                    return
            self.status_label.setText("No next untranslated key found")
        except Exception as exc:
            self.status_label.setText(f"Error: {exc}")

    def _select_key_in_grid(self, filename: str, key: str):
        """Select a specific key in the data grid."""
        try:
            if self.data_grid.current_file != filename:
                self.data_grid.open_file(filename)
            model = self.data_grid.model
            proxy = self.data_grid.proxy
            for row in range(model.rowCount()):
                entry = model.get_entry(row)
                if entry and entry["key"] == key:
                    source_idx = model.index(row, 0)
                    proxy_idx = proxy.mapFromSource(source_idx)
                    self.data_grid.table.selectRow(proxy_idx.row())
                    self.data_grid.table.scrollTo(proxy_idx)
                    self.data_grid._on_selection_changed(None, None)
                    break
        except Exception as exc:
            self.status_label.setText(f"Error selecting key: {exc}")

    def _on_tab_changed(self, index: int):
        """Refresh content when switching tabs."""
        try:
            if index == 1:  # Overview
                self.dashboard.refresh()
                self.status_label.setText("📊 Overview")
            elif index == 3:  # Glossary
                self.glossary_panel.refresh()
                self.status_label.setText("📖 Glossary")
            elif index == 4:  # Key Analysis
                self.key_analysis.refresh()
                self.status_label.setText("🏷️ Key Analysis")
        except Exception as exc:
            self.status_label.setText(f"Error loading tab: {exc}")

    # ── Actions ────────────────────────────────────────────────────────

    def _save_current_file(self):
        """Save the currently open file."""
        try:
            filename = self.data_grid.current_file
            if not filename:
                self.status_label.setText("No file selected to save")
                return

            self.data_grid._save_current_file()
            self.status_label.setText(f"✓ Saved: {filename}")
            self.file_browser.update_item(filename)
        except Exception as exc:
            QMessageBox.critical(self, "Error Saving",
                                 f"Failed to save file:\n{exc}")
            self.status_label.setText(f"Error saving: {exc}")

    def _save_all(self):
        """Save all modified files."""
        try:
            count = self.data_manager.save_all_modified()
            if count > 0:
                self.status_label.setText(f"✓ Saved {count} modified file(s)")
                stats = self.data_manager.get_overall_stats()
                real = self.data_manager.get_real_overall_stats()
                self._update_status_bar(stats, real)
            else:
                self.status_label.setText("No modified files to save")
        except Exception as exc:
            QMessageBox.critical(self, "Error Saving All",
                                 f"Failed to save all files:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    def _reload_all(self):
        """Reload all files from disk."""
        try:
            reply = QMessageBox.question(
                self, "Reload All",
                "Reload all files from disk?\n"
                "Unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            self.data_manager.reload_all()
            self._load_data()
            self.status_label.setText("All files reloaded from disk")
        except Exception as exc:
            QMessageBox.critical(self, "Error Reloading",
                                 f"Failed to reload files:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    def _open_mod_folder(self):
        """Open a different mod folder and load its translations."""
        try:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Mod Folder (root directory or localisation/ subfolder)"
            )
            if not folder:
                return

            file_count = self.data_manager.set_mod_directory(folder)
            self._load_data()

            self.status_label.setText(
                f"Loaded {file_count} .yml files from {folder}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error Opening Mod Folder",
                                 f"Failed to open mod folder:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    def _show_import_dialog(self):
        """Show the Import dialog."""
        try:
            dialog = ImportDialog(self.data_manager, self)
            dialog.exec()
            self.status_label.setText("Import dialog closed")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Import dialog failed:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    def _export_translations(self):
        """Export translations to JSON."""
        try:
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Export Translations",
                "translations_export.json",
                "JSON Files (*.json)"
            )
            if not filepath:
                return

            import json
            report = []
            for fname in self.data_manager.file_names:
                yml = self.data_manager.get_file(fname)
                if yml:
                    for entry in yml.entries:
                        report.append({
                            "file": fname,
                            "key": entry.key,
                            "value": entry.value,
                        })

            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=2)

            QMessageBox.information(
                self, "Export Complete",
                f"Exported {len(report)} entries to:\n{filepath}"
            )
            self.status_label.setText(f"Exported {len(report)} entries")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed",
                                 f"Could not export translations:\n{exc}")
            self.status_label.setText(f"Export failed: {exc}")

    def _show_ai_translate(self):
        """Open the AI Translate dialog for batch translation."""
        try:
            from ..ui.ai_translate_dialog import AITranslateDialog
            dlg = AITranslateDialog(self.data_manager, self)
            dlg.exec()
            self.status_label.setText("AI Translate dialog closed")
        except Exception as exc:
            QMessageBox.critical(self, "Error",
                                 f"AI Translate dialog failed:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    # ── Package / Apply Translation Package ─────────────────────────

    def _package_for_translation(self):
        """Export English-only keys to a JSON package for external translation."""
        try:
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Package for Translation",
                "translation_package.json",
                "Translation Package (*.json)"
            )
            if not filepath:
                return

            from datetime import date
            package = {
                "version": "1.0",
                "exported": str(date.today()),
                "files": {},
            }
            total_keys = 0
            for fname in self.data_manager.file_names:
                yml = self.data_manager.get_file(fname)
                if not yml:
                    continue
                file_keys = {}
                for entry in yml.entries:
                    value = entry.value
                    # Skip if it has Thai text
                    if THAI_RE.search(value):
                        continue
                    # Skip if it's a pure reference (only $VAR$, £icon£, §tags§)
                    if is_pure_reference(value):
                        continue
                    # Only include keys with real English text
                    if value.strip():
                        file_keys[entry.key] = value
                if file_keys:
                    package["files"][fname] = file_keys
                    total_keys += len(file_keys)

            import json
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(package, fh, ensure_ascii=False, indent=2)

            file_count = len(package["files"])
            QMessageBox.information(
                self, "Package Created",
                f"Exported {total_keys} English-only keys across {file_count} files."
            )
            self.status_label.setText(
                f"Packaged {total_keys} keys across {file_count} files"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Package Failed",
                                 f"Could not package translations:\n{exc}")
            self.status_label.setText(f"Package failed: {exc}")

    def _apply_translation_package(self):
        """Import translations from a JSON package created by _package_for_translation."""
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Apply Translation Package",
                "",
                "Translation Package (*.json)"
            )
            if not filepath:
                return

            import json
            with open(filepath, "r", encoding="utf-8") as fh:
                package = json.load(fh)

            applied = 0
            modified_files = set()
            files_data = package.get("files", {})
            for fname, keys in files_data.items():
                yml = self.data_manager.get_file(fname)
                if yml is None:
                    continue
                for key, new_value in keys.items():
                    if yml.set_value(key, new_value):
                        applied += 1
                        modified_files.add(fname)
            for fname in modified_files:
                self.data_manager.save_file(fname)

            file_count = len(modified_files)
            QMessageBox.information(
                self, "Package Applied",
                f"Applied {applied} translations across {file_count} files."
            )
            self.status_label.setText(
                f"Applied {applied} translations across {file_count} files"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Apply Failed",
                                 f"Could not apply translation package:\n{exc}")
            self.status_label.setText(f"Apply failed: {exc}")

    def _show_settings(self):
        """Open the Settings dialog."""
        try:
            from ..ui.settings_dialog import SettingsDialog
            dlg = SettingsDialog(self)
            dlg.exec()
            self.status_label.setText("Settings dialog closed")
        except Exception as exc:
            QMessageBox.critical(self, "Error",
                                 f"Settings dialog failed:\n{exc}")

    def _batch_rename_dialog(self):
        """Dialog for batch renaming a key across all files."""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Batch Rename Key")
            dialog.setMinimumWidth(400)
            layout = QVBoxLayout(dialog)

            layout.addWidget(QLabel("Old Key Name:"))
            old_input = QLineEdit()
            layout.addWidget(old_input)

            layout.addWidget(QLabel("New Key Name:"))
            new_input = QLineEdit()
            layout.addWidget(new_input)

            info = QLabel(
                "This will rename the key in ALL files that contain it."
            )
            info.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()};")
            layout.addWidget(info)

            buttons = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            buttons.addWidget(cancel_btn)

            rename_btn = QPushButton("Rename")
            rename_btn.clicked.connect(dialog.accept)
            rename_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DarkTheme.ACCENT.name()};
                    color: {DarkTheme.BG_PRIMARY.name()};
                    font-weight: bold;
                }}
            """)
            buttons.addWidget(rename_btn)
            layout.addLayout(buttons)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                old_key = old_input.text().strip()
                new_key = new_input.text().strip()
                if old_key and new_key:
                    renamed = 0
                    for fname in self.data_manager.file_names:
                        yml = self.data_manager.get_file(fname)
                        if yml and yml.rename_key(old_key, new_key):
                            yml.save()
                            renamed += 1
                    QMessageBox.information(
                        dialog, "Batch Rename",
                        f"Renamed '{old_key}' to '{new_key}' in "
                        f"{renamed} file(s)."
                    )
                    self.status_label.setText(
                        f"Renamed '{old_key}' to '{new_key}' in {renamed} file(s)"
                    )
                    self._reload_all()
        except Exception as exc:
            QMessageBox.critical(self, "Rename Failed",
                                 f"Batch rename failed:\n{exc}")
            self.status_label.setText(f"Rename failed: {exc}")

    def _run_coverage_check(self):
        """Run the coverage check script and show output."""
        try:
            result = self.data_manager.run_script(
                "tools/check_coverage.py"
            )
            if result["success"]:
                dialog = QDialog(self)
                dialog.setWindowTitle("Coverage Report")
                dialog.setMinimumSize(600, 400)
                layout = QVBoxLayout(dialog)
                text = QTextEdit()
                text.setReadOnly(True)
                text.setFont(QFont("Consolas", 10))
                text.setPlainText(result["stdout"])
                layout.addWidget(text)
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                dialog.exec()
            else:
                QMessageBox.warning(
                    self, "Coverage Check Failed",
                    result.get("error", "Unknown error")
                )
            self.status_label.setText("Coverage check completed")
        except Exception as exc:
            QMessageBox.critical(self, "Coverage Check Error",
                                 f"Failed to run coverage check:\n{exc}")
            self.status_label.setText(f"Error: {exc}")

    def _focus_search(self):
        """Focus the search input in the data grid."""
        try:
            if self._main_tabs.currentIndex() == 0:
                self.data_grid.search_input.setFocus()
                self.data_grid.search_input.selectAll()
        except Exception as exc:
            self.status_label.setText(f"Error: {exc}")

    def _show_shortcuts(self):
        """Show keyboard shortcuts reference."""
        try:
            QMessageBox.information(self, "Keyboard Shortcuts",
                "<h3>⌨️ Keyboard Shortcuts</h3>"
                "<table>"
                "<tr><td><b>Ctrl+1</b></td><td>Editor tab</td></tr>"
                "<tr><td><b>Ctrl+D</b></td><td>Overview tab</td></tr>"
                "<tr><td><b>Ctrl+Shift+F</b></td><td>Search tab</td></tr>"
                "<tr><td><b>Ctrl+G</b></td><td>Glossary tab</td></tr>"
                "<tr><td><b>Ctrl+K</b></td><td>Key Analysis tab</td></tr>"
                "<tr><td></td></tr>"
                "<tr><td><b>Ctrl+S</b></td><td>Save current file</td></tr>"
                "<tr><td><b>Ctrl+Shift+S</b></td><td>Save all modified files</td></tr>"
                "<tr><td><b>Ctrl+R</b></td><td>Reload all files</td></tr>"
                "<tr><td><b>Ctrl+I</b></td><td>Import translations</td></tr>"
                "<tr><td><b>Ctrl+E</b></td><td>Focus editor</td></tr>"
                "<tr><td><b>Ctrl+Return</b></td><td>Save current value</td></tr>"
                "<tr><td><b>Ctrl+Q</b></td><td>Exit</td></tr>"
                "</table>"
            )
        except Exception as exc:
            self.status_label.setText(f"Error: {exc}")

    def _show_about(self):
        """Show the About dialog."""
        try:
            QMessageBox.about(
                self, f"About {self.APP_NAME}",
                f"<h2>{self.APP_NAME} v{self.VERSION}</h2>"
                f"<p style='color: #aaa;'>Stellaris Localisation Editor</p>"
                f"<hr>"
                f"<p style='color: #888; font-size: 10px;'>"
                f"MIT License<br><br>"
                f"Copyright (c) 2026 SLE Project<br><br>"
                f"Permission is hereby granted, free of charge, to any person "
                f"obtaining a copy of this software and associated documentation "
                f"files (the \"Software\"), to deal in the Software without "
                f"restriction, including without limitation the rights to use, "
                f"copy, modify, merge, publish, distribute, sublicense, and/or "
                f"sell copies of the Software.</p>"
            )
        except Exception as exc:
            self.status_label.setText(f"Error showing About: {exc}")

    def _update_status_bar(self, stats: dict, real_stats: dict | None = None):
        """Update status bar with coverage and real quality stats."""
        self.file_count_label.setText(
            f"Files: {stats['total_files']}"
        )

        if real_stats:
            real_pct = real_stats['real_pct']
            self.coverage_status_label.setText(
                f"Real: {real_pct}%"
            )
            if real_pct >= 80:
                c = DarkTheme.ACCENT_GREEN
            elif real_pct >= 50:
                c = DarkTheme.ACCENT_YELLOW
            else:
                c = DarkTheme.ACCENT_RED
            self.coverage_status_label.setStyleSheet(
                f"font-weight: bold; color: {c.name()};"
            )
            self.old_coverage_label.setText(
                f"(old: {stats['overall_pct']}%)"
            )
        else:
            self.coverage_status_label.setText(
                f"Coverage: {stats['overall_pct']}%"
            )
            self.old_coverage_label.setText("")

        modified = self.data_manager.modified_files
        if modified:
            self.modified_label.setText(
                f"⚠️ {len(modified)} unsaved"
            )
            self.modified_label.setStyleSheet(
                f"color: {DarkTheme.ACCENT_YELLOW.name()}; font-weight: bold;"
            )
        else:
            self.modified_label.setText("")

    # ── Window close event ─────────────────────────────────────────

    def closeEvent(self, event):
        """Confirm close if there are unsaved changes."""
        try:
            if self.data_manager.has_modified():
                reply = QMessageBox.question(
                    self, "Unsaved Changes",
                    "There are unsaved changes.\n"
                    "Save before closing?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel,
                )
                if reply == QMessageBox.StandardButton.Save:
                    self._save_all()
                    event.accept()
                elif reply == QMessageBox.StandardButton.Discard:
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
        except Exception:
            event.accept()
