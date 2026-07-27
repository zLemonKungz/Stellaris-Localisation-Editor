"""
Data grid — QTableView with custom model for browsing all keys in a file.
Supports sorting, filtering, inline editing, and keyboard navigation.
"""

from PyQt6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, pyqtSignal, QVariant,
    QSortFilterProxyModel, QSize, QEvent,
)
from PyQt6.QtGui import (
    QColor, QBrush, QFont, QKeySequence, QPainter,
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QLineEdit, QComboBox, QLabel, QPushButton, QFrame,
    QAbstractItemView, QStyledItemDelegate, QStyle, QAbstractItemDelegate,
)
from .themes import coverage_color, DarkTheme, Colors
from ..core.data_manager import DataManager, THAI_RE, is_pure_reference


# ── Custom table model ─────────────────────────────────────────────────────

class TranslationTableModel(QAbstractTableModel):
    """Model holding translation entries for one file."""

    COLUMNS = ["Key Name", "Translation Value", "Status"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[dict] = []  # list of {"key": ..., "value": ...}
        self._filename: str = ""

    def load_entries(self, filename: str, entries: list[dict]):
        self.beginResetModel()
        self._filename = filename
        self._entries = list(entries)
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self._entries.clear()
        self._filename = ""
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._entries):
            return QVariant()

        entry = self._entries[index.row()]
        col = index.column()

        # Determine real status based on content (Thai, reference, english)
        val = entry.get("value", "")
        sv = val.strip()
        if not sv:
            status_text = "✗ Empty"
            is_thai = False
            is_ref = False
        elif THAI_RE.search(val):
            status_text = "✓ Translated"
            is_thai = True
            is_ref = False
        elif is_pure_reference(val):
            status_text = "🔑 Key Ref"
            is_thai = False
            is_ref = True
        else:
            status_text = "⚠️ English"
            is_thai = False
            is_ref = False

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return entry["key"]
            elif col == 1:
                return entry["value"]
            elif col == 2:
                return status_text
        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == 0:
                return f"Key: {entry['key']}"
            elif col == 1:
                prefix = "✓" if is_thai else ("🔑" if is_ref else ("⚠️" if sv else "✗"))
                return f"{prefix} {val[:200]}" if val else "✗ Empty"
        elif role == Qt.ItemDataRole.ForegroundRole:
            if col == 0:
                return QBrush(Colors.KEY_COLOR)
            elif col == 2:
                if is_thai:
                    return QBrush(Colors.COVERAGE_COMPLETE)
                elif is_ref:
                    return QBrush(Colors.REFERENCE_COLOR)
                elif sv:
                    return QBrush(DarkTheme.ACCENT_RED)
                return QBrush(Colors.COVERAGE_LOW)
        elif role == Qt.ItemDataRole.FontRole:
            if col == 0:
                font = QFont("Consolas", 10)
                return font
            font = QFont("Segoe UI", 11)
            if col == 1:
                val = entry.get("value", "")
                # Italic if empty, english-only, or pure reference
                font.setItalic(not val or not val.strip() or not THAI_RE.search(val))
            return font
        elif role == Qt.ItemDataRole.BackgroundRole:
            sv = entry.get("value", "").strip()
            if THAI_RE.search(entry.get("value", "")):
                return QBrush(DarkTheme.ROW_BG_THAI)
            elif is_pure_reference(entry.get("value", "")):
                return QBrush(DarkTheme.ROW_BG_REF)
            elif sv:
                return QBrush(DarkTheme.ROW_BG_ENGLISH)
            return QBrush(DarkTheme.ROW_BG_EMPTY)
        elif role == Qt.ItemDataRole.UserRole:
            # For sorting: 3 = Thai, 2 = Ref, 1 = English-only, 0 = empty
            if col == 0:
                return entry["key"]
            elif col == 1:
                return entry.get("value", "")
            elif col == 2:
                val = entry.get("value", "")
                sv = val.strip()
                if not sv:
                    return 0
                if THAI_RE.search(val):
                    return 3
                if is_pure_reference(val):
                    return 2
                return 1
        elif role == Qt.ItemDataRole.EditRole:
            if col == 1:
                return entry.get("value", "")

        return QVariant()

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole and index.column() == 1:
            entry = self._entries[index.row()]
            new_val = str(value)
            if entry.get("value") != new_val:
                entry["value"] = new_val
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                return True
        return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = super().flags(index)
        if index.column() == 1:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def get_entry(self, row: int) -> dict | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None


# ── Filter proxy ──────────────────────────────────────────────────────────

class TranslationFilterProxy(QSortFilterProxyModel):
    """Filter proxy supporting text search, status filtering, and category."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_text = ""
        self._status_filter = "all"  # all, translated, untranslated
        self._category_filter = ""   # empty = no category filter

    def set_filter_text(self, text: str):
        self._filter_text = text.lower()
        self.invalidateFilter()

    def set_status_filter(self, status: str):
        self._status_filter = status
        self.invalidateFilter()

    def set_category_filter(self, category: str):
        """Filter by key prefix category. Empty = show all."""
        self._category_filter = category.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if not isinstance(model, TranslationTableModel):
            return True
        if row >= len(model._entries):
            return False

        entry = model._entries[row]
        val = entry.get("value", "")
        sv = val.strip()

        # REAL status filter (Thai text detection, not just non-empty)
        if self._status_filter == "translated":
            if not sv or not THAI_RE.search(val):
                return False
        elif self._status_filter == "untranslated":
            if sv and THAI_RE.search(val):
                return False

        # Category filter
        if self._category_filter:
            key_cat = DataManager.category_for_key(entry["key"])
            if key_cat.lower() != self._category_filter:
                return False

        # Text search
        if self._filter_text:
            key = entry["key"].lower()
            value = val.lower()
            if self._filter_text not in key and self._filter_text not in value:
                return False

        return True


# ── Status badge delegate for the Status column ─────────────────────────

class StatusBadgeDelegate(QStyledItemDelegate):
    """Draws colored badge pills for the Status column."""

    BADGE_COLORS = {
        "✓ Translated": (QColor("#27ae60"), QColor("#1a4731")),
        "⚠️ English":   (QColor("#f39c12"), QColor("#4a3a1a")),
        "🔑 Key Ref":   (QColor("#c39bd3"), QColor("#2a1a4a")),
        "✗ Empty":      (QColor("#7f8c8d"), QColor("#3a3a3a")),
    }

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        text = index.data(Qt.ItemDataRole.DisplayRole)
        badge_fg, badge_bg = self.BADGE_COLORS.get(text,
            (DarkTheme.TEXT_PRIMARY, DarkTheme.BG_SURFACE))

        # Background rect
        rect = option.rect.adjusted(4, 3, -4, -3)
        painter.setBrush(badge_bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)

        # Text
        painter.setPen(badge_fg)
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.restore()

    def sizeHint(self, option, index):
        base = super().sizeHint(option, index)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        return QSize(max(base.width() + 16, 90), base.height() + 4)


# ── Delegate for inline editing ───────────────────────────────────────────

class TranslationDelegate(QStyledItemDelegate):
    """Custom delegate for the value column with Stellaris syntax preview."""

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            from PyQt6.QtWidgets import QLineEdit
            editor = QLineEdit(parent)
            editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {DarkTheme.BG_SURFACE.name()};
                    color: {DarkTheme.TEXT_PRIMARY.name()};
                    border: 2px solid {DarkTheme.ACCENT.name()};
                    font-family: 'Consolas', 'Noto Sans Thai', monospace;
                    font-size: 13px;
                    padding: 4px;
                }}
            """)
            editor.installEventFilter(self)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == 1:
            value = index.model().data(index, Qt.ItemDataRole.EditRole)
            editor.setText(str(value) if value else "")

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)

    def eventFilter(self, obj, event):
        """Handle Enter=save and Escape=cancel for inline editing."""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.commitData.emit(obj)
                self.closeEditor.emit(obj, QAbstractItemDelegate.EndEditHint.NoHint)
                return True
            if event.key() == Qt.Key.Key_Escape:
                self.closeEditor.emit(obj, QAbstractItemDelegate.EndEditHint.NoHint)
                return True
        return super().eventFilter(obj, event)


# ── Main DataGrid Widget ──────────────────────────────────────────────────

class DataGrid(QWidget):
    """
    Main data grid widget — shows all keys for a selected file with
    filtering, sorting, and inline editing capabilities.
    """

    value_changed = pyqtSignal(str, str)  # key, new_value
    file_opened = pyqtSignal(str)         # filename

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.current_file: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: bold;
            padding: 4px 8px;
            color: {DarkTheme.ACCENT.name()};
        """)
        toolbar.addWidget(self.file_label)
        toolbar.addStretch()

        self.coverage_label = QLabel("")
        self.coverage_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_SECONDARY.name()};
            font-size: 12px;
            padding: 4px 8px;
        """)
        toolbar.addWidget(self.coverage_label)

        # Row count
        self.row_count_label = QLabel("")
        self.row_count_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()};
            font-size: 12px;
        """)
        toolbar.addWidget(self.row_count_label)

        layout.addLayout(toolbar)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search keys / values...")
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_bar.addWidget(self.search_input, 1)

        self.save_btn = QPushButton("💾 Save File")
        self.save_btn.clicked.connect(self._save_current_file)
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT_GREEN.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold;
                padding: 6px 18px;
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
        filter_bar.addWidget(self.save_btn)

        layout.addLayout(filter_bar)

        # Table view
        self.model = TranslationTableModel(self)
        self.proxy = TranslationFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setItemDelegate(TranslationDelegate(self))
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setColumnWidth(0, 280)

        # Status badge delegate (colored pill badges)
        self.table.setItemDelegateForColumn(2, StatusBadgeDelegate(self))

        # Connect selection change to emit signal
        self.table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        # Connect model changes to enable save button
        self.model.dataChanged.connect(self._on_data_changed)

        layout.addWidget(self.table)

    def open_file(self, filename: str):
        """Load and display entries from a file."""
        yml = self.data_manager.get_file(filename)
        if yml is None:
            self.clear()
            return

        self.current_file = filename
        entries = [e.to_dict() for e in yml.entries]
        self.model.load_entries(filename, entries)
        self.file_label.setText(f"📄 {filename}")

        # Show REAL coverage (Thai text detection)
        real = self.data_manager.get_real_coverage(filename)
        if real:
            pct_color = coverage_color(real["thai_pct"])
            self.coverage_label.setText(
                f"Real: {real['thai_pct']}%"
                f" | {real['has_thai']} Thai / {real['english_only']} EN / {real['empty']} Empty"
            )
            self.coverage_label.setStyleSheet(
                f"color: {pct_color.name()}; font-size: 12px; font-weight: bold;"
            )
        self.row_count_label.setText(f"  ({len(entries)} keys)")

        self.save_btn.setEnabled(False)
        self.search_input.clear()

        self.file_opened.emit(filename)

    def clear(self):
        """Clear the table."""
        self.model.clear()
        self.current_file = ""
        self.file_label.setText("No file selected")
        self.coverage_label.setText("")
        self.row_count_label.setText("")
        self.save_btn.setEnabled(False)

    def _on_search_changed(self, text: str):
        try:
            self.proxy.set_filter_text(text)
            self.row_count_label.setText(
                f"  ({self.proxy.rowCount()} visible)"
            )
        except Exception:
            pass

    def _on_selection_changed(self, selected, deselected):
        """Emit signal when a row is selected."""
        try:
            indexes = self.table.selectionModel().selectedRows(0)
            if indexes:
                source_index = self.proxy.mapToSource(indexes[0])
                entry = self.model.get_entry(source_index.row())
                if entry:
                    self.value_changed.emit(entry["key"], entry.get("value", ""))
        except Exception:
            pass

    def _on_data_changed(self, top_left, bottom_right, roles):
        try:
            self.save_btn.setEnabled(True)
            if self.current_file:
                self.data_manager.on_value_changed(self.current_file)
        except Exception:
            pass

    def _save_current_file(self):
        try:
            if not self.current_file:
                return

            updates = {}
            for entry in self.model._entries:
                updates[entry["key"]] = entry["value"]

            yml = self.data_manager.get_file(self.current_file)
            if yml:
                yml.set_values(updates)
                self.data_manager.save_file(self.current_file)
                self.save_btn.setEnabled(False)

                real = self.data_manager.get_real_coverage(self.current_file)
                if real:
                    self.coverage_label.setText(
                        f"Real: {real['thai_pct']}%"
                        f" | {real['has_thai']} Thai / {real['english_only']} EN / {real['empty']} Empty"
                    )
        except Exception:
            pass

    def get_selected_key(self) -> str | None:
        """Get the key of the currently selected row."""
        indexes = self.table.selectionModel().selectedRows(0)
        if indexes:
            source_index = self.proxy.mapToSource(indexes[0])
            entry = self.model.get_entry(source_index.row())
            return entry["key"] if entry else None
        return None

    def update_value(self, key: str, value: str):
        """Update a value in the model (called from editor panel)."""
        for i, entry in enumerate(self.model._entries):
            if entry["key"] == key:
                idx = self.model.index(i, 1)
                self.model.setData(idx, value, Qt.ItemDataRole.EditRole)
                return

    def _jump_to_key(self):
        """Jump to a specific key in the data grid."""
        try:
            key_text = self.jump_input.text().strip()
            if not key_text:
                return
            model = self.model
            proxy = self.proxy
            for row in range(model.rowCount()):
                entry = model.get_entry(row)
                if entry and key_text.lower() in entry["key"].lower():
                    source_idx = model.index(row, 0)
                    proxy_idx = proxy.mapFromSource(source_idx)
                    self.table.selectRow(proxy_idx.row())
                    self.table.scrollTo(proxy_idx)
                    self.jump_input.clear()
                    return
        except Exception:
            pass
