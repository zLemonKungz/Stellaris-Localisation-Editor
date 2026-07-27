"""
Glossary panel — browse and search the authoritative glossary of Stellaris
terms with their Thai translations, grouped by category.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QFrame, QAbstractItemView,
)

from .themes import DarkTheme, Colors


class GlossaryPanel(QWidget):
    """Panel for browsing the Stellaris Thai translation glossary."""

    term_selected = pyqtSignal(str)  # English term

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("📖 Glossary")
        header.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        layout.addWidget(header)

        subtitle = QLabel("~80 authoritative Stellaris term translations")
        subtitle.setStyleSheet(f"""
            font-size: 12px;
            color: {DarkTheme.TEXT_SECONDARY.name()};
            margin-bottom: 4px;
        """)
        layout.addWidget(subtitle)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search glossary terms...")
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        # Category filter
        cat_layout = QHBoxLayout()
        cat_label = QLabel("Category:")
        cat_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()};
            font-size: 12px;
        """)
        cat_layout.addWidget(cat_label)

        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All")
        self.cat_combo.currentTextChanged.connect(self._apply_filter)
        cat_layout.addWidget(self.cat_combo)
        cat_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Reload")
        self.refresh_btn.clicked.connect(self.refresh)
        cat_layout.addWidget(self.refresh_btn)

        layout.addLayout(cat_layout)

        # Glossary tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["English", "ไทย", "Notes"])
        self.tree.setColumnCount(3)
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(28)
        self.tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tree.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tree.header().setStretchLastSection(True)
        self.tree.setStyleSheet(f"""
            QTreeWidget::item {{
                padding: 6px 8px 6px 4px;
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {DarkTheme.TABLE_SELECTION.name()};
                border: 1px solid {DarkTheme.ACCENT.name()};
            }}
        """)

        layout.addWidget(self.tree, 1)

        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()};
            font-size: 11px;
            padding: 4px;
        """)
        layout.addWidget(self.info_label)

    def refresh(self):
        """Load glossary data (from built-in + external) and populate the tree."""
        self.tree.clear()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("All")

        # Use built-in glossary (embedded in code, always available)
        from ..core.glossary_data import BUILTIN_GLOSSARY
        grouped = {}
        for entry in BUILTIN_GLOSSARY:
            cat = entry.get("category", "uncategorized")
            grouped.setdefault(cat, []).append(entry)
        categories = sorted(grouped.keys())

        for cat in categories:
            self.cat_combo.addItem(cat.capitalize())
            cat_item = QTreeWidgetItem(self.tree, [cat.capitalize()])
            cat_item.setExpanded(False)
            cat_item.setFirstColumnSpanned(True)

            font = cat_item.font(0)
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            cat_item.setFont(0, font)
            cat_item.setForeground(0, DarkTheme.ACCENT)
            cat_item.setBackground(0, DarkTheme.BG_TERTIARY)
            # Add a faint bottom border via rich text in the tooltip area
            cat_item.setToolTip(0, f"Category: {cat.capitalize()} — {len(grouped[cat])} terms")

            for entry in sorted(grouped[cat], key=lambda x: x["english"]):
                eng = entry.get("english", "")
                thai = entry.get("thai", "")
                alt = entry.get("alt", "")
                notes = entry.get("notes", "")

                display_thai = thai
                if alt:
                    display_thai += f" (หรือ {alt})"

                child = QTreeWidgetItem(cat_item, [eng, display_thai, notes])

                # Color the English term
                child.setForeground(0, Colors.KEY_COLOR)
                child.setForeground(1, DarkTheme.ACCENT_GREEN)

                # Tooltip
                tooltip = f"Category: {cat}\n"
                if alt:
                    tooltip += f"Alternative: {alt}\n"
                if notes:
                    tooltip += f"Notes: {notes}\n"
                child.setToolTip(0, tooltip)
                child.setToolTip(1, tooltip)

        self.cat_combo.blockSignals(False)
        self._update_info()

    def _apply_filter(self, *args):
        """Apply search text and category filter."""
        try:
            search = self.search_input.text().strip().lower()
            category = self.cat_combo.currentText().lower()

            for i in range(self.tree.topLevelItemCount()):
                cat_item = self.tree.topLevelItem(i)
                cat_name = cat_item.text(0).lower()

                cat_match = category == "all" or category == cat_name
                cat_item.setHidden(not cat_match)

                if not cat_match:
                    continue

                visible_count = 0
                for j in range(cat_item.childCount()):
                    child = cat_item.child(j)
                    eng = child.text(0).lower()
                    thai = child.text(1).lower()
                    match = not search or search in eng or search in thai
                    child.setHidden(not match)
                    if match:
                        visible_count += 1

                if visible_count > 0:
                    cat_item.setExpanded(True)
                else:
                    cat_item.setHidden(not cat_match and visible_count == 0)

            self._update_info()
        except Exception:
            pass

    def _update_info(self):
        """Update the info label with counts."""
        from ..core.glossary_data import BUILTIN_GLOSSARY
        self.info_label.setText(
            f"{len(BUILTIN_GLOSSARY)} terms in glossary"
        )
