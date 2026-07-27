"""
File browser panel — tree view of .yml files with coverage color-coding.
Supports filtering, right-click context menu, and drag-to-reorder.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont, QAction
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QLineEdit, QLabel, QHeaderView, QMenu, QPushButton,
    QHBoxLayout, QFrame,
)

from .themes import coverage_color, DarkTheme


class FileTreeItem(QTreeWidgetItem):
    """Tree item that stores REAL coverage data (Thai text detection)."""

    def __init__(self, filename: str, coverage: dict):
        super().__init__()
        self.filename = filename
        self.coverage = coverage  # real coverage: {total, has_thai, english_only, empty, thai_pct}
        self._update_display()

    def _update_display(self):
        thai_pct = self.coverage["thai_pct"]
        total = self.coverage["total"]
        has_thai = self.coverage["has_thai"]
        english_only = self.coverage["english_only"]

        # Emoji prefix based on REAL Thai coverage
        if thai_pct >= 100:
            prefix = "🟢"
        elif thai_pct >= 50:
            prefix = "🟡"
        elif thai_pct > 0:
            prefix = "🔴"
        else:
            prefix = "⚫"

        # Clean display: colored dot + filename only
        display = f"{prefix} {self.filename}"

        self.setText(0, display)
        self.setToolTip(0,
            f"{self.filename}\n"
            f"Total: {total:,} keys\n"
            f"✓ Thai: {has_thai:,}\n"
            f"✗ English only: {english_only:,}\n"
            f"Coverage: {thai_pct}%"
        )

        # Color-code based on REAL Thai coverage
        color = coverage_color(thai_pct)
        self.setForeground(0, QBrush(color))

        font = self.font(0)
        font.setBold(thai_pct >= 100)
        self.setFont(0, font)

        self.setData(0, Qt.ItemDataRole.UserRole, thai_pct)

    def update_coverage(self, coverage: dict):
        self.coverage = coverage
        self._update_display()

    def __lt__(self, other):
        """Sort by real coverage percentage (for tree sort)."""
        if isinstance(other, FileTreeItem):
            return self.coverage["thai_pct"] < other.coverage["thai_pct"]
        return super().__lt__(other)


class FileBrowser(QWidget):
    """
    File browser panel showing all .yml files with coverage indicators.
    Emits file_selected when a file is clicked.
    """

    file_selected = pyqtSignal(str)  # filename
    file_double_clicked = pyqtSignal(str)

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._items: dict[str, FileTreeItem] = {}  # filename -> item
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(3)

        # Filter — minimal
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter files...")
        self.filter_input.setClearButtonEnabled(True)
        self.filter_input.textChanged.connect(self._on_filter_changed)
        self.filter_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 5px 10px;
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 5px;
                background-color: {DarkTheme.BG_SURFACE.name()};
                color: {DarkTheme.TEXT_PRIMARY.name()};
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.filter_input)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAnimated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.tree.setIndentation(0)
        self.tree.setSelectionMode(
            QTreeWidget.SelectionMode.SingleSelection
        )
        self.tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(
            lambda item, col: self.file_double_clicked.emit(
                item.filename if isinstance(item, FileTreeItem) else ""
            )
        )

        layout.addWidget(self.tree, 1)

    def refresh(self):
        """Reload file list with REAL coverage (Thai text detection)."""
        self.tree.clear()
        self._items.clear()
        self.tree.setSortingEnabled(False)

        coverage = self.data_manager.get_all_real_coverage()
        if not coverage:
            return

        for fname in sorted(coverage.keys()):
            cov = coverage[fname]
            item = FileTreeItem(fname, cov)
            self.tree.addTopLevelItem(item)
            self._items[fname] = item

        # Sort by coverage% descending (worst-first by default)
        self.tree.setSortingEnabled(True)
        self.tree.sortItems(0, Qt.SortOrder.DescendingOrder)

        self._apply_filter()

    def _apply_filter(self):
        """Apply current filter text to the tree."""
        text = self.filter_input.text().strip().lower()
        for fname, item in self._items.items():
            item.setHidden(text not in fname.lower() if text else False)

    def _on_filter_changed(self, text: str):
        try:
            self._apply_filter()
        except Exception:
            pass

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        try:
            if isinstance(item, FileTreeItem):
                self.file_selected.emit(item.filename)
        except Exception:
            pass

    def _show_context_menu(self, pos):
        try:
            item = self.tree.itemAt(pos)
            if not isinstance(item, FileTreeItem):
                return

            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background-color: {DarkTheme.BG_SECONDARY.name()};
                    color: {DarkTheme.TEXT_PRIMARY.name()};
                    border: 1px solid {DarkTheme.BORDER.name()};
                }}
                QMenu::item:selected {{
                    background-color: {DarkTheme.BG_SURFACE.name()};
                }}
            """)

            open_action = menu.addAction("📄 Open File")
            open_action.triggered.connect(
                lambda: self.file_double_clicked.emit(item.filename)
            )

            reload_action = menu.addAction("🔄 Reload from Disk")
            reload_action.triggered.connect(lambda: self._reload_file(item.filename))

            menu.exec(self.tree.viewport().mapToGlobal(pos))
        except Exception:
            pass

    def _reload_file(self, filename: str):
        self.data_manager.reload_file(filename)
        cov = self.data_manager.get_real_coverage(filename)
        if cov and filename in self._items:
            self._items[filename].update_coverage(cov)
        self._apply_filter()

    def select_file(self, filename: str):
        """Programmatically select a file in the tree."""
        if filename in self._items:
            self.tree.setCurrentItem(self._items[filename])
            self.tree.scrollToItem(self._items[filename])

    def update_item(self, filename: str):
        """Update a single item's REAL coverage after edits."""
        cov = self.data_manager.get_real_coverage(filename)
        if cov and filename in self._items:
            self._items[filename].update_coverage(cov)
        self._update_stats()
