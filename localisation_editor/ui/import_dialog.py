"""
Import dialog — import translations from external sources:
- English game source files (generate stubs for new DLCs)
- JSON files (key-value pairs)
- CSV files (spreadsheet exports)
- Another mod's .yml files
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTabWidget, QWidget, QMessageBox,
    QLineEdit, QCheckBox, QGroupBox, QTextEdit, QComboBox,
    QApplication,
)

from .themes import DarkTheme


class ImportDialog(QDialog):
    """Dialog for importing translations from external sources."""

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setWindowTitle("Import Translations")
        self.setMinimumSize(600, 450)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DarkTheme.BG_PRIMARY.name()};
                color: {DarkTheme.TEXT_PRIMARY.name()};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QLabel("📥 Import Translations")
        header.setStyleSheet(f"""
            font-size: 18px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        # ── Tab 1: From English Source ──
        src_tab = QWidget()
        src_layout = QVBoxLayout(src_tab)

        src_info = QLabel(
            "Import English .yml files from the Stellaris game directory.\n"
            "New files will be created as stubs. Existing files will have "
            "new keys added (with empty values)."
        )
        src_info.setWordWrap(True)
        src_info.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY.name()}; font-size: 13px;")
        src_layout.addWidget(src_info)

        # Source directory selector
        dir_row = QHBoxLayout()
        self.src_path = QLineEdit()
        self.src_path.setPlaceholderText("Choose the Stellaris English locale folder...")
        dir_row.addWidget(self.src_path, 1)
        browse_btn = QPushButton("📂 Browse...")
        browse_btn.clicked.connect(self._browse_source_dir)
        dir_row.addWidget(browse_btn)
        src_layout.addLayout(dir_row)

        tip = QLabel(
            "Tip: Usually found at:\n"
            "  Steam\\steamapps\\common\\Stellaris\\localisation\\english\\"
        )
        tip.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 12px;")
        src_layout.addWidget(tip)

        src_layout.addStretch()

        self.dry_run_cb = QCheckBox("Dry run (preview only, don't write files)")
        self.dry_run_cb.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;")
        src_layout.addWidget(self.dry_run_cb)

        run_btn = QPushButton("🚀 Import from English Source")
        run_btn.clicked.connect(self._do_import_source)
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold; padding: 8px;
                border-radius: 4px;
            }}
        """)
        src_layout.addWidget(run_btn)

        tabs.addTab(src_tab, "🎮 English Source")

        # ── Tab 2: From JSON/CSV ──
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)

        data_info = QLabel(
            "Import translations from a JSON or CSV file.\n\n"
            "JSON format:\n"
            "  [{\"key\": \"KEY_NAME\", \"value\": \"Translation\"}, ...]\n"
            "  or {\"KEY_NAME\": \"Translation\", ...}\n\n"
            "CSV format:\n"
            "  Columns: key, value (or Key, Value, text, translation, thai)"
        )
        data_info.setWordWrap(True)
        data_info.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY.name()}; font-size: 13px;")
        data_layout.addWidget(data_info)

        file_row = QHBoxLayout()
        self.data_path = QLineEdit()
        self.data_path.setPlaceholderText("Choose a JSON or CSV file...")
        file_row.addWidget(self.data_path, 1)
        browse_data = QPushButton("📂 Browse...")
        browse_data.clicked.connect(self._browse_data_file)
        file_row.addWidget(browse_data)
        data_layout.addLayout(file_row)

        # Target file selector
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target mod file (optional):"))
        self.target_combo = QComboBox()
        self.target_combo.addItem("All files (auto-detect keys)")
        for fname in self.data_manager.file_names:
            self.target_combo.addItem(fname)
        target_row.addWidget(self.target_combo, 1)
        data_layout.addLayout(target_row)

        data_layout.addStretch()

        import_data_btn = QPushButton("📥 Import from File")
        import_data_btn.clicked.connect(self._do_import_data)
        import_data_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold; padding: 8px;
                border-radius: 4px;
            }}
        """)
        data_layout.addWidget(import_data_btn)

        tabs.addTab(data_tab, "📄 JSON / CSV")

        # ── Tab 3: YML File ──
        yml_tab = QWidget()
        yml_layout = QVBoxLayout(yml_tab)
        yml_layout.setSpacing(10)

        yml_info = QLabel(
            "Import translations from another mod's .yml file.\n"
            "The file must have the same name as a target file in your mod.\n"
            "If the target file doesn't exist, a new one will be created."
        )
        yml_info.setWordWrap(True)
        yml_info.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY.name()}; font-size: 13px;")
        yml_layout.addWidget(yml_info)

        yml_row = QHBoxLayout()
        self.yml_path = QLineEdit()
        self.yml_path.setPlaceholderText("Choose a .yml file from another mod...")
        yml_row.addWidget(self.yml_path, 1)
        browse_yml = QPushButton("📂 Browse...")
        browse_yml.clicked.connect(self._browse_yml_file)
        yml_row.addWidget(browse_yml)
        yml_layout.addLayout(yml_row)

        yml_layout.addStretch()

        import_yml_btn = QPushButton("📥 Import from YML")
        import_yml_btn.clicked.connect(self._do_import_yml)
        import_yml_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold; padding: 8px 16px;
                border-radius: 4px; font-size: 13px;
            }}
        """)
        yml_layout.addWidget(import_yml_btn)

        tabs.addTab(yml_tab, "📁 YML File")

        # ── Tab 4: From Mod Directory ──
        mod_tab = QWidget()
        mod_layout = QVBoxLayout(mod_tab)
        mod_layout.setSpacing(10)

        mod_info = QLabel(
            "Import all .yml files from another mod at once.\n"
            "The tool will find all matching files by name and import "
            "the translations automatically."
        )
        mod_info.setWordWrap(True)
        mod_info.setStyleSheet(f"color: {DarkTheme.TEXT_SECONDARY.name()}; font-size: 13px;")
        mod_layout.addWidget(mod_info)

        mod_row = QHBoxLayout()
        self.mod_path = QLineEdit()
        self.mod_path.setPlaceholderText("Choose a mod folder to import from...")
        mod_row.addWidget(self.mod_path, 1)
        browse_mod = QPushButton("📂 Browse...")
        browse_mod.clicked.connect(self._browse_mod_dir)
        mod_row.addWidget(browse_mod)
        mod_layout.addLayout(mod_row)

        mod_layout.addSpacing(8)

        self.only_thai_cb = QCheckBox("Only bring in values that have Thai text")
        self.only_thai_cb.setChecked(True)
        self.only_thai_cb.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;")
        mod_layout.addWidget(self.only_thai_cb)

        self.import_empty_cb = QCheckBox("Also bring in empty values (overwrites existing)")
        self.import_empty_cb.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px;")
        mod_layout.addWidget(self.import_empty_cb)

        mod_layout.addStretch()

        import_mod_btn = QPushButton("📥 Import All from Mod")
        import_mod_btn.clicked.connect(self._do_import_mod)
        import_mod_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold; padding: 8px 16px;
                border-radius: 4px; font-size: 13px;
            }}
        """)
        mod_layout.addWidget(import_mod_btn)

        tabs.addTab(mod_tab, "📂 Entire Mod")

        layout.addWidget(tabs, 1)

        # Output log
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        self.output_log.setMaximumHeight(120)
        self.output_log.setStyleSheet(f"""
            background-color: {DarkTheme.BG_SURFACE.name()};
            color: {DarkTheme.TEXT_PRIMARY.name()};
            font-family: Consolas, monospace; font-size: 11px;
            border: 1px solid {DarkTheme.BORDER.name()};
        """)
        layout.addWidget(self.output_log)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _log(self, msg: str):
        self.output_log.append(msg)

    def _browse_source_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select English Locale Directory")
        if path:
            self.src_path.setText(path)
            # Preview files found
            p = Path(path)
            ymls = list(p.glob("*_l_english.yml"))
            self._log(f"Found {len(ymls)} .yml files in {path}")

    def _browse_data_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select JSON or CSV File",
            "", "Data Files (*.json *.csv);;JSON (*.json);;CSV (*.csv)"
        )
        if path:
            self.data_path.setText(path)
            self._log(f"Selected: {path}")

    def _browse_yml_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select .yml File",
            "", "YML Files (*.yml)"
        )
        if path:
            self.yml_path.setText(path)
            self._log(f"Selected: {path}")

    def _do_import_source(self):
        try:
            path = self.src_path.text().strip()
            if not path:
                QMessageBox.warning(self, "No Directory", "Please select a source directory first.")
                return

            src_dir = Path(path)
            if not src_dir.exists():
                QMessageBox.warning(self, "Invalid Path", "Directory does not exist.")
                return

            dry_run = self.dry_run_cb.isChecked()
            result = self.data_manager.import_from_english_source(src_dir, dry_run=dry_run)

            if "error" in result:
                self._log(f"❌ Error: {result['error']}")
                return

            created = result.get("created", [])
            updated = result.get("updated", [])
            skipped = result.get("skipped", 0)
            total = result.get("total", 0)

            self._log(f"📊 Total files: {total}")
            self._log(f"✅ Created: {len(created)} files")
            self._log(f"🔄 Updated: {len(updated)} files")
            self._log(f"⏭️ Skipped: {skipped}")

            for f in created[:5]:
                self._log(f"  + {f}")
            if len(created) > 5:
                self._log(f"  ... and {len(created)-5} more")

            if not dry_run and (created or updated):
                self.data_manager.reload_all()
        except Exception as exc:
            self._log(f"❌ Error: {exc}")

    def _do_import_data(self):
        try:
            path = self.data_path.text().strip()
            if not path:
                QMessageBox.warning(self, "No File", "Please select a data file first.")
                return

            filepath = Path(path)
            if not filepath.exists():
                QMessageBox.warning(self, "Invalid Path", "File does not exist.")
                return

            target = ""
            if self.target_combo.currentIndex() > 0:
                target = self.target_combo.currentText()

            if filepath.suffix.lower() == ".json":
                result = self.data_manager.import_from_json(filepath, target)
            elif filepath.suffix.lower() == ".csv":
                result = self.data_manager.import_from_csv(filepath, target)
            else:
                self._log(f"❌ Unsupported file type: {filepath.suffix}")
                return

            if "error" in result:
                self._log(f"❌ Error: {result['error']}")
                return

            imported = result.get("imported", 0)
            total = result.get("total_keys", 0)
            files = result.get("files_affected", [])

            self._log(f"📊 Total keys in file: {total}")
            self._log(f"✅ Imported: {imported} keys")
            self._log(f"📁 Files affected: {len(files)}")

            if imported > 0:
                self.data_manager.reload_all()
        except Exception as exc:
            self._log(f"❌ Error: {exc}")

    def _do_import_yml(self):
        try:
            path = self.yml_path.text().strip()
            if not path:
                QMessageBox.warning(self, "No File", "Please select a .yml file first.")
                return

            filepath = Path(path)
            if not filepath.exists():
                QMessageBox.warning(self, "Invalid Path", "File does not exist.")
                return

            result = self.data_manager.import_from_yml(filepath)
            if "error" in result:
                self._log(f"❌ Error: {result['error']}")
                return

            imported = result.get("imported", 0)
            is_new = result.get("new_file", False)
            target = result.get("target", "")

            if is_new:
                self._log(f"✅ Created new file: {target} ({imported} keys)")
            else:
                self._log(f"✅ Imported {imported} Thai keys into {target}")

            if imported > 0:
                self.data_manager.reload_all()
        except Exception as exc:
            self._log(f"❌ Error: {exc}")

    def _browse_mod_dir(self):
        """Browse for a mod directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Mod Directory")
        if path:
            self.mod_path.setText(path)
            p = Path(path)
            ymls = list(p.rglob("*_l_english.yml"))
            self._log(f"Found {len(ymls)} .yml files in {path}")
            if ymls:
                self._log(f"  e.g. {ymls[0].name}")

    def _do_import_mod(self):
        """Batch import all files from a mod directory."""
        try:
            path = self.mod_path.text().strip()
            if not path:
                QMessageBox.warning(self, "No Directory",
                                    "Please select a mod directory first.")
                return
            mod_dir = Path(path)
            if not mod_dir.exists():
                QMessageBox.warning(self, "Invalid Path",
                                    "Directory does not exist.")
                return

            import_empty = self.import_empty_cb.isChecked()
            only_thai = self.only_thai_cb.isChecked()

            self._log(f"📂 Scanning {mod_dir.name} for .yml files...")
            QApplication.processEvents()

            result = self.data_manager.import_from_mod_directory(
                mod_dir,
                import_empty=import_empty,
                only_thai=only_thai,
            )

            if "error" in result:
                self._log(f"❌ Error: {result['error']}")
                return

            self._log(f"📊 Found {result['total_found']} .yml files")
            self._log(f"✅ Imported {result['imported_files']} files ({result['total_keys']:,} keys)")
            if result.get("skipped_files"):
                self._log(f"⏭️  Skipped {len(result['skipped_files'])} files")
            if result.get("errors"):
                self._log(f"❌ Errors ({len(result['errors'])}):")
                for e in result["errors"][:5]:
                    self._log(f"  {e}")
        except Exception as exc:
            self._log(f"❌ Error: {exc}")
