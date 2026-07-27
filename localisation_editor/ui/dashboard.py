"""
Dashboard panel — shows translation quality using real Thai text detection.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QGroupBox, QStackedWidget,
)

from .themes import DarkTheme, coverage_color, Colors
from ..core.data_manager import THAI_RE, is_pure_reference


class StatCard(QFrame):
    """A small card showing a single statistic with label."""

    def __init__(self, label: str, value: str, color: QColor = None,
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(150, 80)

        border = color or DarkTheme.BORDER
        self.setStyleSheet(f"""
            StatCard {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                border: none;
                border-left: 3px solid {border.name()};
                border-radius: 8px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        self.label = QLabel(label)
        self.label.setStyleSheet(f"""
            font-size: 11px;
            color: {DarkTheme.TEXT_MUTED.name()};
        """)
        layout.addWidget(self.label)

        self.value = QLabel(value)
        self.value.setStyleSheet(f"""
            font-size: 26px;
            font-weight: bold;
            color: {DarkTheme.TEXT_PRIMARY.name()};
        """)
        layout.addWidget(self.value)

        if subtitle:
            self.subtitle = QLabel(subtitle)
            self.subtitle.setStyleSheet(f"""
                font-size: 11px;
                color: {DarkTheme.TEXT_SECONDARY.name()};
            """)
            layout.addWidget(self.subtitle)

    def set_value(self, value: str):
        self.value.setText(value)


class MiniBar(QProgressBar):
    """Compact progress bar for showing a single percentage."""

    def __init__(self, pct: float = 0, parent=None):
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(int(pct))
        self.setFormat(f"{pct}%")
        self.setTextVisible(True)
        self.setFixedHeight(22)


class BigCoverageDisplay(QFrame):
    """Hero display showing the REAL coverage percentage in large text."""

    def __init__(self, pct: int = 0, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(90)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        # Large percentage number
        self.pct_label = QLabel("---")
        self.pct_label.setStyleSheet(f"""
            font-size: 52px; font-weight: bold;
            color: {DarkTheme.ACCENT_GREEN.name()};
        """)
        layout.addWidget(self.pct_label)

        # Label + subtitle
        text_box = QVBoxLayout()
        text_box.setSpacing(0)
        title = QLabel("REAL Thai Translation Coverage")
        title.setStyleSheet(f"""
            font-size: 16px; font-weight: bold;
            color: {DarkTheme.TEXT_PRIMARY.name()};
        """)
        text_box.addWidget(title)
        self.sub = QLabel("Detects actual Thai text — not just non-empty values")
        self.sub.setStyleSheet(f"""
            font-size: 11px;
            color: {DarkTheme.TEXT_MUTED.name()};
        """)
        text_box.addWidget(self.sub)
        layout.addLayout(text_box, 1)

        self._stripe_color = Colors.COVERAGE_COMPLETE

    def set_pct(self, pct: int):
        self.pct_label.setText(f"{pct}%")
        if pct >= 80:
            color = Colors.COVERAGE_COMPLETE
        elif pct >= 50:
            color = Colors.COVERAGE_HIGH
        else:
            color = Colors.COVERAGE_LOW
        self._stripe_color = color
        self.pct_label.setStyleSheet(f"""
            font-size: 52px; font-weight: bold;
            color: {color.name()};
        """)
        self.setStyleSheet(f"""
            BigCoverageDisplay {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                border: 2px solid {color.name()};
                border-radius: 10px;
                padding: 0;
            }}
        """)
        self.sub.setText(
            f"{'✅ Great!' if pct >= 80 else ('⚠️ Needs work' if pct >= 50 else '❌ Critical')}"
        )


# ── Dashboard ──

class Dashboard(QWidget):
    """Dashboard showing REAL translation quality — Thai content detection."""

    navigate_to = pyqtSignal(str, str)  # filename, key

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Header ──
        header = QLabel("📊 Overview")
        header.setStyleSheet(f"""
            font-size: 18px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
            padding-bottom: 4px;
        """)
        layout.addWidget(header)

        # ── Stacked content: empty state (0) vs stats (1) ──
        self._content_stack = QStackedWidget()

        # Page 0: No mod folder opened
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(6)
        empty_name = QLabel("SLE")
        empty_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_name.setStyleSheet(f"""
            font-size: 38px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
        """)
        empty_layout.addWidget(empty_name)
        empty_sub = QLabel("Open a mod folder to view translation statistics")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_sub.setStyleSheet(f"""
            font-size: 15px;
            color: {DarkTheme.TEXT_MUTED.name()};
        """)
        empty_layout.addWidget(empty_sub)
        self._content_stack.addWidget(empty_page)  # index 0

        # Page 1: Stats content
        content_page = QWidget()
        content_layout = QVBoxLayout(content_page)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        # ════════════════════════════════════════════════════════════
        # HERO ROW: Big % + 3 stat chips side by side
        # ════════════════════════════════════════════════════════════
        hero_row = QHBoxLayout()
        hero_row.setSpacing(10)

        # Big coverage number on the left
        self.hero_display = BigCoverageDisplay(0)
        self.hero_display.setMinimumWidth(200)
        hero_row.addWidget(self.hero_display)

        # Stat chips on the right
        stats_col = QVBoxLayout()
        stats_col.setSpacing(6)

        def make_chip(label, color, obj_name):
            chip = QFrame()
            chip.setStyleSheet(f"""
                QFrame#{obj_name} {{
                    background: {DarkTheme.BG_SURFACE.name()};
                    border-left: 3px solid {color.name()};
                    border-radius: 6px;
                    padding: 8px 12px;
                }}
            """)
            chip.setObjectName(obj_name)
            chip.setMinimumHeight(50)
            cl = QHBoxLayout(chip)
            cl.setContentsMargins(12, 6, 12, 6)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 11px;")
            cl.addWidget(lbl)
            val = QLabel("--")
            val.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 22px; font-weight: bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            cl.addWidget(val, 1)
            setattr(self, obj_name, val)
            return chip

        stats_col.addWidget(make_chip("Total Keys",        DarkTheme.TEXT_MUTED,    "_total_val"))
        stats_col.addWidget(make_chip("Thai ✓",            Colors.COVERAGE_COMPLETE,"_thai_val"))
        stats_col.addWidget(make_chip("English ✗",         Colors.COVERAGE_LOW,     "_eng_val"))

        hero_row.addLayout(stats_col, 1)
        content_layout.addLayout(hero_row)

        # ═══ Progress bar ═══
        self.real_bar = MiniBar(0)
        self.real_bar.setFixedHeight(26)
        self.real_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                border: 1px solid {DarkTheme.BORDER.name()};
                border-radius: 4px; text-align: center;
                font-size: 12px; font-weight: bold;
                color: {DarkTheme.TEXT_PRIMARY.name()};
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {Colors.COVERAGE_HIGH.name()},
                    stop:1 {Colors.COVERAGE_LOW.name()});
                border-radius: 3px;
            }}
        """)
        content_layout.addWidget(self.real_bar)

        # ── separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {DarkTheme.BORDER.name()};")
        content_layout.addWidget(sep)

        # ════════════════════════════════════════════════════════════
        # FILE TABLE + SORT
        # ════════════════════════════════════════════════════════════
        table_header_row = QHBoxLayout()
        th = QLabel("Coverage per File")
        th.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px; font-weight: bold;")
        table_header_row.addWidget(th)
        table_header_row.addStretch()
        sl = QLabel("Sort:")
        sl.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 11px;")
        table_header_row.addWidget(sl)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Worst first", "Best first", "Name A-Z"])
        self.sort_combo.currentIndexChanged.connect(self._refresh_file_table)
        table_header_row.addWidget(self.sort_combo)
        content_layout.addLayout(table_header_row)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["File", "Total", "Thai ✓", "Real %"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.verticalHeader().hide()
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.itemClicked.connect(self._on_file_row_clicked)
        content_layout.addWidget(self.file_table, 1)

        # ── separator ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {DarkTheme.BORDER.name()};")
        content_layout.addWidget(sep2)

        # ════════════════════════════════════════════════════════════
        # ENGLISH-ONLY KEYS DETAIL
        # ════════════════════════════════════════════════════════════
        detail_header_row = QHBoxLayout()
        dh = QLabel("English-Only Keys")
        dh.setStyleSheet(f"color: {DarkTheme.TEXT_PRIMARY.name()}; font-size: 13px; font-weight: bold;")
        detail_header_row.addWidget(dh)
        self.detail_header = QLabel("(click a file row)")
        self.detail_header.setStyleSheet(f"color: {DarkTheme.TEXT_MUTED.name()}; font-size: 11px;")
        detail_header_row.addWidget(self.detail_header)
        detail_header_row.addStretch()
        content_layout.addLayout(detail_header_row)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(2)
        self.detail_table.setHorizontalHeaderLabels(["Key", "Current Value"])
        self.detail_table.horizontalHeader().setStretchLastSection(True)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.detail_table.verticalHeader().hide()
        self.detail_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.detail_table.itemDoubleClicked.connect(self._on_detail_double_click)
        content_layout.addWidget(self.detail_table, 1)

        self._content_stack.addWidget(content_page)  # index 1
        layout.addWidget(self._content_stack, 1)

    # ── Refresh ──

    def refresh(self):
        """Load real coverage data and populate the dashboard."""
        if not self.data_manager.has_mod_folder:
            self._content_stack.setCurrentIndex(0)  # show empty state
            return

        self._content_stack.setCurrentIndex(1)  # show stats
        real = self.data_manager.get_real_overall_stats()

        # Hero display
        self.hero_display.set_pct(int(real['real_pct']))

        # Cards
        rp = real['real_pct']
        self._total_val.setText(f"{real['total_keys']:,}")
        self._thai_val.setText(f"{real['has_thai']:,}")
        eng_pct = real['english_only'] / max(real['total_keys'], 1) * 100
        self._eng_val.setText(f"{real['english_only']:,} ({eng_pct:.1f}%)")

        # Bar
        self.real_bar.setValue(int(rp))
        self.real_bar.setFormat(f"{rp}%")

        # File table
        self._refresh_file_table()

    def _set_filter(self, mode: str):
        """Toggle filter buttons and refresh."""
        try:
            self._current_filter = mode
            self._refresh_file_table()
        except Exception:
            pass

    def _refresh_file_table(self):
        """Populate the per-file coverage table."""
        try:
            import re
            self._current_filter = getattr(self, '_current_filter', 'all')
            real_cov = self.data_manager.get_all_real_coverage()
            if not real_cov:
                return

            files = []
            for fname, rc in real_cov.items():
                files.append((fname, rc))

            # Sort
            sort_idx = self.sort_combo.currentIndex()
            if sort_idx == 0:  # Worst first
                files.sort(key=lambda x: x[1]['thai_pct'])
            elif sort_idx == 1:  # Best first
                files.sort(key=lambda x: x[1]['thai_pct'], reverse=True)
            else:  # Name A-Z
                files.sort(key=lambda x: x[0].lower())

            self.file_table.setRowCount(len(files))
            for row, (fname, rc) in enumerate(files):
                tc = rc['thai_pct']
                color = coverage_color(tc)

                self.file_table.setItem(row, 0, QTableWidgetItem(fname))
                self.file_table.setItem(row, 1, QTableWidgetItem(str(rc['total'])))
                self.file_table.setItem(row, 2, QTableWidgetItem(str(rc['has_thai'])))

                pct_item = QTableWidgetItem(f"{tc}%")
                pct_item.setForeground(color)
                self.file_table.setItem(row, 3, pct_item)

                # Color the file name based on coverage
                fn_item = self.file_table.item(row, 0)
                if fn_item:
                    fn_item.setForeground(color)

        except Exception:
            pass

    def _on_file_row_clicked(self, item: QTableWidgetItem):
        """Show English-only keys for the clicked file."""
        try:
            row = item.row()
            fname_item = self.file_table.item(row, 0)
            if not fname_item:
                return
            filename = fname_item.text()
            cov = self.data_manager.get_real_coverage(filename)
            if not cov:
                return

            self.detail_header.setText(f"English-only keys in: {filename}")
            yml = self.data_manager.get_file(filename)
            if not yml:
                return

            english_keys = []
            for entry in yml.entries:
                val = entry.value.strip()
                if not val:
                    continue
                if THAI_RE.search(val):
                    continue
                if is_pure_reference(val):
                    continue
                english_keys.append((entry.key, val))

            self.detail_table.setRowCount(len(english_keys))
            for row2, (key, val) in enumerate(english_keys):
                self.detail_table.setItem(row2, 0, QTableWidgetItem(key))
                self.detail_table.setItem(row2, 1, QTableWidgetItem(val[:80]))
        except Exception:
            pass

    def _on_detail_double_click(self, item: QTableWidgetItem):
        """Navigate to editor for a specific key."""
        try:
            row = item.row()
            key_item = self.detail_table.item(row, 0)
            if not key_item:
                return
            key = key_item.text()
            # Get the filename from the file table selection
            selection = self.file_table.selectedItems()
            if not selection:
                return
            fname_item = self.file_table.item(selection[0].row(), 0)
            if not fname_item:
                return
            self.navigate_to.emit(fname_item.text(), key)
        except Exception:
            pass
