"""
Search dialog — global full-text search across all translation files.
Supports searching in keys and/or values, filtering by status,
and batch operations.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QCheckBox, QGroupBox, QFrame, QAbstractItemView,
    QProgressBar,
)

from .themes import DarkTheme, coverage_color, Colors
from ..core.data_manager import THAI_RE


class SearchPanel(QWidget):
    """Search panel for global search across all translation files."""

    navigate_to = pyqtSignal(str, str)  # filename, key

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._results: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("🔍 Global Search")
        header.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        layout.addWidget(header)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search keys or values across all files..."
        )
        self.search_input.setStyleSheet(f"""
            font-size: 16px;
            padding: 12px 16px;
            background-color: {DarkTheme.BG_SURFACE.name()};
            border: 2px solid {DarkTheme.BORDER.name()};
            border-radius: 8px;
        """)
        self.search_input.setMinimumHeight(44)
        self.search_input.returnPressed.connect(self._do_search)
        search_row.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("🔎 Search")
        self.search_btn.clicked.connect(self._do_search)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold;
                padding: 10px 28px;
                border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #74b9ff;
            }}
        """)
        search_row.addWidget(self.search_btn)

        layout.addLayout(search_row)

        # Options row
        options_row = QHBoxLayout()
        options_row.setSpacing(16)

        # Scope
        scope_group = QGroupBox("Search in")
        scope_group.setStyleSheet(f"""
            QGroupBox {{
                color: {DarkTheme.TEXT_PRIMARY.name()};
                font-size: 12px;
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 6px;
                margin-top: 10px;
                padding: 8px;
            }}
        """)
        scope_layout = QHBoxLayout(scope_group)

        self.search_keys = QCheckBox("Keys")
        self.search_keys.setChecked(True)
        scope_layout.addWidget(self.search_keys)

        self.search_values = QCheckBox("Values")
        self.search_values.setChecked(True)
        scope_layout.addWidget(self.search_values)

        options_row.addWidget(scope_group)

        # Status filter
        status_group = QGroupBox("Status")
        status_group.setStyleSheet(scope_group.styleSheet())
        status_layout = QHBoxLayout(status_group)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Translated Only",
                                    "Untranslated Only"])
        status_layout.addWidget(self.status_combo)

        options_row.addWidget(status_group)

        # Case sensitivity
        self.case_sensitive = QCheckBox("Case sensitive")
        self.case_sensitive.setStyleSheet(f"""
            color: {DarkTheme.TEXT_PRIMARY.name()};
        """)
        options_row.addWidget(self.case_sensitive)

        options_row.addStretch()

        layout.addLayout(options_row)

        # Results info
        result_header = QHBoxLayout()
        self.result_count = QLabel("Enter a search query to begin.")
        self.result_count.setStyleSheet(f"""
            color: {DarkTheme.TEXT_SECONDARY.name()};
            font-size: 14px;
            font-weight: bold;
            padding: 4px 0;
        """)
        result_header.addWidget(self.result_count, 1)

        layout.addLayout(result_header)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["File", "Key", "Current Value", "Status"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.itemDoubleClicked.connect(self._on_result_double_click)

        layout.addWidget(self.table, 1)

    def _do_search(self):
        """Execute the search."""
        try:
            query = self.search_input.text().strip()
            if not query:
                return

            results = self.data_manager.search(
                query,
                scope="all",
                case_sensitive=self.case_sensitive.isChecked()
            )

            # Apply additional filters
            status_filter = self.status_combo.currentText()
            filtered = []
            for r in results:
                # Scope filter
                if not self.search_keys.isChecked() and r["match_key"]:
                    continue
                if not self.search_values.isChecked() and r["match_value"]:
                    continue

                # Status filter — real Thai detection
                val = r.get("value", "")
                is_empty = not val.strip()
                has_thai = bool(val.strip() and THAI_RE.search(val))
                if status_filter == "Translated Only" and not has_thai:
                    continue
                if status_filter == "Untranslated Only" and (is_empty or has_thai):
                    continue

                filtered.append(r)

            self._results = filtered
            self._populate_table()
        except Exception:
            pass

    def _populate_table(self):
        """Populate the results table."""
        self.table.setRowCount(len(self._results))
        self.result_count.setText(
            f"Found {len(self._results)} matching key(s)."
        )

        for row, r in enumerate(self._results):
            # File
            file_item = QTableWidgetItem(r["filename"])
            file_item.setToolTip(r["filename"])
            self.table.setItem(row, 0, file_item)

            # Key
            key_item = QTableWidgetItem(r["key"])
            key_item.setForeground(Colors.KEY_COLOR)
            self.table.setItem(row, 1, key_item)

            # Value
            val = r.get("value", "")
            val_item = QTableWidgetItem(val[:80] + "..." if len(val) > 80 else val)
            val_item.setToolTip(val)
            if not val or not val.strip():
                val_item.setForeground(DarkTheme.TEXT_MUTED)
                font = val_item.font()
                font.setItalic(True)
                val_item.setFont(font)
            self.table.setItem(row, 2, val_item)

            # Status — real Thai text detection
            is_empty = not val.strip()
            has_thai = bool(val.strip() and THAI_RE.search(val))
            if is_empty:
                status_text = "✗ Empty"
                status_color = DarkTheme.TEXT_MUTED
            elif has_thai:
                status_text = "✓ Translated"
                status_color = Colors.COVERAGE_COMPLETE
            else:
                status_text = "✗ English Only"
                status_color = Colors.COVERAGE_LOW
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(status_color)
            self.table.setItem(row, 3, status_item)

            # Store metadata
            for item in [file_item, key_item, val_item, status_item]:
                item.setData(Qt.ItemDataRole.UserRole, row)

    def _on_result_double_click(self, item: QTableWidgetItem):
        """Navigate to the selected result."""
        try:
            row = item.data(Qt.ItemDataRole.UserRole)
            if row is not None and 0 <= row < len(self._results):
                r = self._results[row]
                self.navigate_to.emit(r["filename"], r["key"])
        except Exception:
            pass
