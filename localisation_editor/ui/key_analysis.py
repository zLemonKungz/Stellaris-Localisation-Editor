"""
Key Analysis panel — browse keys sorted by category/prefix, view coverage
by category, variable usage stats, long keys, and more.
Provides convenience features like bulk operations by category.
"""

from collections import defaultdict

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QComboBox,
    QFrame, QAbstractItemView, QGroupBox, QGridLayout, QProgressBar,
    QSplitter, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox,
)

from .themes import DarkTheme, coverage_color, Colors


class KeyAnalysisPanel(QWidget):
    """
    Key Analysis panel — categorize, filter, and browse keys by:
    - Prefix category (trait_, civic_, tech_, etc.)
    - Variable usage
    - Value characteristics (color tags, icons, length)
    - Coverage per category
    """

    navigate_to = pyqtSignal(str, str)  # filename, key

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._current_category: str = ""
        self._category_results: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("🏷️ Key Analysis & Categorization")
        header.setStyleSheet(f"""
            font-size: 20px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        layout.addWidget(header)

        subtitle = QLabel(
            "Browse keys by type (traits, civics, techs, etc.), filter by "
            "characteristics, and track coverage per category"
        )
        subtitle.setStyleSheet(f"""
            font-size: 12px; color: {DarkTheme.TEXT_SECONDARY.name()};
            margin-bottom: 4px;
        """)
        layout.addWidget(subtitle)

        # Multi-tab: Categories | Variables | Long Keys | Untranslated
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        # ── Tab 1: Category Coverage ──
        cat_tab = QWidget()
        cat_layout = QVBoxLayout(cat_tab)
        cat_layout.setContentsMargins(8, 8, 8, 8)
        self._build_category_tab(cat_layout)
        tabs.addTab(cat_tab, "📂 By Category")

        # ── Tab 2: Variable Stats ──
        var_tab = QWidget()
        var_layout = QVBoxLayout(var_tab)
        var_layout.setContentsMargins(8, 8, 8, 8)
        self._build_variable_tab(var_layout)
        tabs.addTab(var_tab, "🔣 Variables & Tags")

        # ── Tab 3: Long Keys ──
        long_tab = QWidget()
        long_layout = QVBoxLayout(long_tab)
        long_layout.setContentsMargins(8, 8, 8, 8)
        self._build_longkeys_tab(long_layout)
        tabs.addTab(long_tab, "📄 Long Keys")

        layout.addWidget(tabs, 1)

        # ── Bottom: category detail ──
        detail_group = QGroupBox("Category Detail")
        detail_group.setStyleSheet(f"""
            QGroupBox {{
                color: {DarkTheme.TEXT_PRIMARY.name()};
                font-size: 13px; font-weight: bold;
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 6px; margin-top: 10px; padding: 12px;
            }}
        """)
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setSpacing(4)

        detail_header = QHBoxLayout()
        self.detail_title = QLabel("Select a category to view keys")
        self.detail_title.setStyleSheet(f"""
            font-size: 14px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        detail_header.addWidget(self.detail_title, 1)

        self.detail_count = QLabel("")
        self.detail_count.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()}; font-size: 12px;
        """)
        detail_header.addWidget(self.detail_count)

        detail_layout.addLayout(detail_header)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(
            ["Key", "Value (preview)", "File", "Characteristics"]
        )
        self.detail_table.horizontalHeader().setStretchLastSection(False)
        self.detail_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.detail_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.detail_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.detail_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.detail_table.verticalHeader().hide()
        self.detail_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.detail_table.itemDoubleClicked.connect(
            self._on_detail_double_click
        )
        detail_layout.addWidget(self.detail_table, 1)

        # Action buttons for the detail view
        action_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 Filter within this category...")
        self.filter_input.textChanged.connect(self._filter_detail)
        action_row.addWidget(self.filter_input, 1)

        self.show_untranslated_btn = QPushButton("Only Untranslated")
        self.show_untranslated_btn.setCheckable(True)
        self.show_untranslated_btn.toggled.connect(self._toggle_untranslated_filter)
        action_row.addWidget(self.show_untranslated_btn)

        self.open_btn = QPushButton("📂 Open in Editor")
        self.open_btn.clicked.connect(self._open_selected_in_editor)
        self.open_btn.setEnabled(False)
        action_row.addWidget(self.open_btn)

        detail_layout.addLayout(action_row)

        layout.addWidget(detail_group)

    # ── Tab 1: Category Coverage ──

    def _build_category_tab(self, layout):
        # Summary cards
        self.cat_grid = QGridLayout()
        self.cat_grid.setSpacing(8)

        self.total_cat_label = self._make_stat_card("Total Categories", "--")
        self.cat_grid.addWidget(self.total_cat_label, 0, 0)

        self.cat_keys_label = self._make_stat_card("Keys in Categories", "--")
        self.cat_grid.addWidget(self.cat_keys_label, 0, 1)

        self.cat_coverage_label = self._make_stat_card("Category Coverage", "--")
        self.cat_grid.addWidget(self.cat_coverage_label, 0, 2)

        layout.addLayout(self.cat_grid)

        # Category tree with coverage
        self.cat_tree = QTreeWidget()
        self.cat_tree.setHeaderLabels(
            ["Category", "Total Keys", "Translated", "Untranslated",
             "Coverage", "Bar"]
        )
        self.cat_tree.setColumnCount(6)
        self.cat_tree.setAlternatingRowColors(True)
        self.cat_tree.setRootIsDecorated(False)
        self.cat_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.cat_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.cat_tree.header().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        self.cat_tree.itemClicked.connect(self._on_category_clicked)

        layout.addWidget(self.cat_tree, 1)

    def _make_stat_card(self, label, value):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 8px; padding: 8px;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 8, 12, 8)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"""
            font-size: 11px; color: {DarkTheme.TEXT_MUTED.name()};
        """)
        cl.addWidget(lbl)
        val = QLabel(value)
        val.setObjectName("stat_value")
        val.setStyleSheet(f"""
            font-size: 22px; font-weight: bold;
            color: {DarkTheme.TEXT_PRIMARY.name()};
        """)
        cl.addWidget(val)
        return card

    # ── Tab 2: Variable / Tag stats ──

    def _build_variable_tab(self, layout):
        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)

        self.var_count_card = self._make_stat_card("Keys with $VAR$", "--")
        stats_grid.addWidget(self.var_count_card, 0, 0)

        self.icon_count_card = self._make_stat_card("Keys with £icon£", "--")
        stats_grid.addWidget(self.icon_count_card, 0, 1)

        self.color_count_card = self._make_stat_card("Keys with §color§", "--")
        stats_grid.addWidget(self.color_count_card, 0, 2)

        self.long_count_card = self._make_stat_card("Long Keys (500+)", "--")
        stats_grid.addWidget(self.long_count_card, 0, 3)

        layout.addLayout(stats_grid)

        # Variable pattern examples
        info_label = QLabel(
            "Game variables ($VALUE$, $NAME|Y$, etc.) are dynamic values "
            "substituted by the game engine. Color tags (§R...§!) apply "
            "text coloring. Icons (£energy£, £pop£, etc.) are inline icons."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_SECONDARY.name()};
            font-size: 12px; padding: 8px;
            background-color: {DarkTheme.BG_SURFACE.name()};
            border-radius: 6px; border: 1px solid {DarkTheme.BORDER.name()};
        """)
        layout.addWidget(info_label)

        # Key table for variable-heavy keys
        var_table_header = QLabel("Keys with the most variables (sample):")
        var_table_header.setStyleSheet(f"""
            font-size: 13px; font-weight: bold;
            color: {DarkTheme.TEXT_PRIMARY.name()}; margin-top: 8px;
        """)
        layout.addWidget(var_table_header)

        self.var_table = QTableWidget()
        self.var_table.setColumnCount(4)
        self.var_table.setHorizontalHeaderLabels(
            ["Key", "File", "Variables Found", "Value Preview"]
        )
        self.var_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.var_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.var_table.setAlternatingRowColors(True)
        self.var_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.var_table.verticalHeader().hide()
        self.var_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.var_table.itemDoubleClicked.connect(self._on_detail_double_click)
        layout.addWidget(self.var_table, 1)

    # ── Tab 3: Long Keys ──

    def _build_longkeys_tab(self, layout):
        header_label = QLabel(
            "Long translation keys (>500 characters) — event descriptions, "
            "tooltips, etc."
        )
        header_label.setStyleSheet(f"""
            font-size: 13px; color: {DarkTheme.TEXT_PRIMARY.name()};
        """)
        layout.addWidget(header_label)

        self.long_table = QTableWidget()
        self.long_table.setColumnCount(4)
        self.long_table.setHorizontalHeaderLabels(
            ["Key", "Length", "File", "Value Preview"]
        )
        self.long_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.long_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.long_table.setAlternatingRowColors(True)
        self.long_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.long_table.verticalHeader().hide()
        self.long_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.long_table.itemDoubleClicked.connect(self._on_detail_double_click)
        layout.addWidget(self.long_table, 1)

    # ── Data Loading ──

    def refresh(self):
        """Run analysis and populate all tabs."""
        import re
        analysis = self.data_manager.get_key_analysis()

        # ── Category tab ──
        self.cat_tree.clear()
        num_cats = len(analysis["categories"])
        total_categorized = sum(
            c["total"] for c in analysis["categories"]
            if c["name"] != "Other"
        )

        self.total_cat_label.findChild(QLabel, "stat_value").setText(
            str(num_cats)
        )
        self.cat_keys_label.findChild(QLabel, "stat_value").setText(
            f"{total_categorized:,}"
        )

        # Calculate average coverage
        cats_with_keys = [c for c in analysis["categories"] if c["total"] > 0]
        if cats_with_keys:
            avg_cov = sum(c["pct"] for c in cats_with_keys) / len(cats_with_keys)
        else:
            avg_cov = 0
        self.cat_coverage_label.findChild(QLabel, "stat_value").setText(
            f"{avg_cov:.1f}%"
        )

        # Populate tree
        for cat in analysis["categories"]:
            item = QTreeWidgetItem([
                cat["name"],
                f"{cat['total']:,}",
                f"{cat['filled']:,}",
                f"{cat['empty']:,}",
                f"{cat['pct']}%",
                "",  # bar placeholder
            ])
            # Color code full row by coverage
            color = coverage_color(cat["pct"])
            for col in range(item.columnCount()):
                if col == 0:
                    item.setForeground(col, DarkTheme.ACCENT if cat["name"] == "Other" else color)
                elif col == 5:
                    pass  # bar placeholder
                else:
                    item.setForeground(col, color)

            # Tooltip
            item.setToolTip(0,
                f"{cat['name']}\n"
                f"Total: {cat['total']:,}\n"
                f"Filled: {cat['filled']:,}\n"
                f"Empty: {cat['empty']:,}\n"
                f"Coverage: {cat['pct']}%"
            )
            self.cat_tree.addTopLevelItem(item)

        self.cat_tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.cat_tree.sortItems(1, Qt.SortOrder.DescendingOrder)

        # ── Variable tab ──
        vs = analysis["variable_stats"]
        self.var_count_card.findChild(QLabel, "stat_value").setText(
            f"{vs['with_vars']:,} ({vs['var_pct']}%)"
        )
        self.icon_count_card.findChild(QLabel, "stat_value").setText(
            f"{vs['with_icons']:,} ({vs['icon_pct']}%)"
        )
        self.color_count_card.findChild(QLabel, "stat_value").setText(
            f"{vs['with_color']:,} ({vs['color_pct']}%)"
        )
        self.long_count_card.findChild(QLabel, "stat_value").setText(
            f"{vs['long_keys']:,}"
        )

        # Variable-heavy keys sample
        var_rows = []
        var_re = re.compile(r"\$[A-Za-z0-9_|]+?\$")
        for fname in self.data_manager.file_names:
            yml = self.data_manager.get_file(fname)
            if not yml:
                continue
            for entry in yml.entries:
                vars_found = var_re.findall(entry.value)
                if len(vars_found) >= 3:
                    var_rows.append({
                        "key": entry.key,
                        "file": fname,
                        "vars": ",".join(set(vars_found)),
                        "var_count": len(set(vars_found)),
                        "value": entry.value[:80],
                    })
        var_rows.sort(key=lambda r: -r["var_count"])

        self.var_table.setRowCount(min(len(var_rows), 100))
        for row, r in enumerate(var_rows[:100]):
            self.var_table.setItem(row, 0, QTableWidgetItem(r["key"]))
            self.var_table.setItem(row, 1, QTableWidgetItem(r["file"]))
            self.var_table.setItem(row, 2, QTableWidgetItem(r["vars"][:60]))
            preview = QTableWidgetItem(r["value"])
            preview.setToolTip(r["value"])
            self.var_table.setItem(row, 3, preview)
            self.var_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, (r["file"], r["key"])
            )

        # ── Long Keys tab ──
        long_rows = []
        for fname in self.data_manager.file_names:
            yml = self.data_manager.get_file(fname)
            if not yml:
                continue
            for entry in yml.entries:
                if len(entry.value) > 500:
                    long_rows.append({
                        "key": entry.key,
                        "length": len(entry.value),
                        "file": fname,
                        "value": entry.value[:80],
                    })
        long_rows.sort(key=lambda r: -r["length"])

        self.long_table.setRowCount(min(len(long_rows), 200))
        for row, r in enumerate(long_rows[:200]):
            self.long_table.setItem(
                row, 0, QTableWidgetItem(r["key"])
            )
            len_item = QTableWidgetItem(f"{r['length']:,}")
            len_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
            )
            self.long_table.setItem(row, 1, len_item)
            self.long_table.setItem(row, 2, QTableWidgetItem(r["file"]))
            preview = QTableWidgetItem(r["value"])
            preview.setToolTip(r["value"])
            self.long_table.setItem(row, 3, preview)
            self.long_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, (r["file"], r["key"])
            )

    # ── Event Handlers ──

    def _on_category_clicked(self, item: QTreeWidgetItem, column: int):
        """Show keys for the clicked category."""
        try:
            category = item.text(0)
            self._current_category = category

            results = self.data_manager.search_by_category(category)
            self._category_results = results
            self._populate_detail_table(results)

            self.detail_title.setText(f"📂 {category}")
            filled = sum(1 for r in results if not r["empty"])
            self.detail_count.setText(
                f"{len(results):,} keys ({filled:,} translated, "
                f"{len(results) - filled:,} untranslated)"
            )
            self.filter_input.clear()
            self.show_untranslated_btn.setChecked(False)
        except Exception:
            pass

    def _populate_detail_table(self, results: list[dict]):
        """Fill the detail table with results."""
        try:
            import re
            self.detail_table.setRowCount(len(results))
            for row, r in enumerate(results):
                key_item = QTableWidgetItem(r["key"])
                key_item.setForeground(Colors.KEY_COLOR)
                key_font = key_item.font()
                key_font.setBold(True)
                key_font.setPointSize(max(key_font.pointSize(), 12))
                key_item.setFont(key_font)
                self.detail_table.setItem(row, 0, key_item)

                val = r["value"][:80] + "..." if len(r["value"]) > 80 else r["value"]
                val_item = QTableWidgetItem(val)
                val_item.setToolTip(r["value"])
                if r["empty"]:
                    val_item.setForeground(DarkTheme.TEXT_MUTED)
                    font = val_item.font()
                    font.setItalic(True)
                    val_item.setFont(font)
                self.detail_table.setItem(row, 1, val_item)

                self.detail_table.setItem(
                    row, 2, QTableWidgetItem(r["filename"])
                )

                chars = []
                if re.search(r"\$[A-Za-z0-9_|]+?\$", r["value"]):
                    chars.append("$VAR$")
                if "£" in r["value"]:
                    chars.append("£icon£")
                if "§" in r["value"]:
                    chars.append("§color§")
                if len(r["value"]) > 500:
                    chars.append("LONG")
                char_text = " ".join(chars) if chars else ""
                char_item = QTableWidgetItem(char_text)
                if chars:
                    char_item.setForeground(DarkTheme.ACCENT_PURPLE)
                self.detail_table.setItem(row, 3, char_item)

                key_item.setData(
                    Qt.ItemDataRole.UserRole,
                    (r["filename"], r["key"])
                )
        except Exception:
            pass

    def _filter_detail(self, text: str):
        """Filter detail table by key/value text."""
        try:
            text = text.lower()
            for row in range(self.detail_table.rowCount()):
                key_item = self.detail_table.item(row, 0)
                val_item = self.detail_table.item(row, 1)
                if key_item and val_item:
                    match = text in key_item.text().lower() or \
                            text in val_item.text().lower()
                    self.detail_table.setRowHidden(row, not match)
        except Exception:
            pass

    def _toggle_untranslated_filter(self, checked: bool):
        """Toggle showing only untranslated keys."""
        try:
            for row in range(self.detail_table.rowCount()):
                key_item = self.detail_table.item(row, 0)
                val_item = self.detail_table.item(row, 1)
                if key_item and val_item:
                    is_empty = val_item.text().startswith("(empty)")
                    hidden = checked and not is_empty
                    self.detail_table.setRowHidden(row, hidden)
        except Exception:
            pass

    def _on_detail_double_click(self, item: QTableWidgetItem):
        """Navigate to the key in the editor."""
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                filename, key = data
                self.navigate_to.emit(filename, key)
        except Exception:
            pass

    def _open_selected_in_editor(self):
        """Open selected key in the editor."""
        try:
            rows = self.detail_table.selectionModel().selectedRows(0)
            if rows:
                data = rows[0].data(Qt.ItemDataRole.UserRole)
                if data:
                    self.navigate_to.emit(data[0], data[1])
        except Exception:
            pass
