"""
Color themes and styling constants for the Localisation Editor.
Provides a modern dark theme and a light theme, plus shared constants.
"""

from PyQt6.QtGui import QColor, QFont


# ── Color Palette ─────────────────────────────────────────────────────────

class Colors:
    """Shared color constants."""

    # Coverage indicators
    COVERAGE_COMPLETE = QColor("#27ae60")       # green: 100%
    COVERAGE_HIGH = QColor("#f39c12")           # yellow/orange: 50-99%
    COVERAGE_LOW = QColor("#e74c3c")            # red: <50%
    COVERAGE_NONE = QColor("#7f8c8d")           # gray: 0%

    # Syntax highlighting
    SYNTAX_VARIABLE = QColor("#e67e22")          # $VAR$ orange
    SYNTAX_ICON = QColor("#9b59b6")              # £icon£ purple
    SYNTAX_COLOR_TAG = QColor("#3498db")         # §...§! blue
    SYNTAX_COLOR_TAG_R = QColor("#e74c3c")       # §R red
    SYNTAX_COLOR_TAG_G = QColor("#27ae60")       # §G green
    SYNTAX_COLOR_TAG_Y = QColor("#f1c40f")       # §Y yellow
    SYNTAX_COLOR_TAG_H = QColor("#00bcd4")       # §H highlight cyan
    SYNTAX_COLOR_TAG_L = QColor("#95a5a6")       # §L lore gray

    # Key column
    KEY_COLOR = QColor("#8e44ad")                # key names
    REFERENCE_COLOR = QColor("#c39bd3")          # key reference ($KEY$) - brighter purple


class DarkTheme:
    """Dark theme color scheme."""

    BG_PRIMARY = QColor("#1e1e2e")
    BG_SECONDARY = QColor("#181825")
    BG_TERTIARY = QColor("#11111b")
    BG_SURFACE = QColor("#252540")

    TEXT_PRIMARY = QColor("#cdd6f4")
    TEXT_SECONDARY = QColor("#bac2de")
    TEXT_MUTED = QColor("#6c7086")

    ACCENT = QColor("#89b4fa")
    ACCENT_BLUE = ACCENT                           # alias for clarity
    ACCENT_GREEN = QColor("#a6e3a1")
    ACCENT_RED = QColor("#f38ba8")
    ACCENT_YELLOW = QColor("#f9e2af")
    ACCENT_ORANGE = QColor("#fab387")
    ACCENT_PURPLE = QColor("#cba6f7")

    # Row background tints (very subtle alpha — applied over alternating base)
    ROW_BG_THAI = QColor(166, 227, 161, 20)        # ACCENT_GREEN @ 20-alpha
    ROW_BG_ENGLISH = QColor(243, 139, 168, 25)     # ACCENT_RED @ 25-alpha
    ROW_BG_EMPTY = QColor(249, 226, 175, 25)       # ACCENT_YELLOW @ 25-alpha
    ROW_BG_REF = QColor(203, 166, 247, 20)         # ACCENT_PURPLE @ 20-alpha

    BORDER = QColor("#313244")

    # Table
    TABLE_ROW_EVEN = QColor("#1e1e2e")
    TABLE_ROW_ODD = QColor("#252540")
    TABLE_SELECTION = QColor("#45475a")
    TABLE_HEADER = QColor("#181825")

    # Scrollbar
    SCROLLBAR_BG = QColor("#181825")
    SCROLLBAR_FG = QColor("#45475a")

    # Editor
    EDITOR_BG = QColor("#1e1e2e")
    EDITOR_TEXT = QColor("#cdd6f4")
    EDITOR_LINE_NUM = QColor("#6c7086")
    EDITOR_CURSOR = QColor("#cdd6f4")

    # Status bar
    STATUS_BG = QColor("#181825")

    @classmethod
    def stylesheet(cls) -> str:
        return f"""
        QMainWindow {{
            background-color: {cls.BG_PRIMARY.name()};
            color: {cls.TEXT_PRIMARY.name()};
        }}
        QWidget {{
            background-color: {cls.BG_PRIMARY.name()};
            color: {cls.TEXT_PRIMARY.name()};
            font-family: 'Segoe UI', 'Noto Sans Thai', sans-serif;
            font-size: 14px;
        }}
        QMenuBar {{
            background-color: {cls.BG_SECONDARY.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border-bottom: 1px solid {cls.BORDER.name()};
            padding: 2px;
        }}
        QMenuBar::item:selected {{
            background-color: {cls.BG_SURFACE.name()};
        }}
        QMenu {{
            background-color: {cls.BG_SECONDARY.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
        }}
        QMenu::item:selected {{
            background-color: {cls.BG_SURFACE.name()};
        }}
        QToolBar {{
            background-color: {cls.BG_SECONDARY.name()};
            border-bottom: 1px solid {cls.BORDER.name()};
            spacing: 6px;
            padding: 4px;
        }}
        QToolButton {{
            background-color: transparent;
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px 10px;
            margin: 1px;
        }}
        QToolButton:hover {{
            background-color: {cls.BG_SURFACE.name()};
            border-color: {cls.BORDER.name()};
        }}
        QToolButton:pressed {{
            background-color: {cls.ACCENT.name()};
            color: {cls.BG_PRIMARY.name()};
        }}
        QStatusBar {{
            background-color: {cls.STATUS_BG.name()};
            color: {cls.TEXT_SECONDARY.name()};
            border-top: 1px solid {cls.BORDER.name()};
            font-size: 11px;
            padding: 2px 10px;
        }}
        QStatusBar::item {{
            border: none;
        }}
        QTreeWidget {{
            background-color: {cls.BG_SECONDARY.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 6px 8px;
            border-radius: 3px;
        }}
        QTreeWidget::item:selected {{
            background-color: {cls.TABLE_SELECTION.name()};
        }}
        QTreeWidget::item:hover {{
            background-color: {cls.BG_SURFACE.name()};
        }}
        QHeaderView::section {{
            background-color: {cls.TABLE_HEADER.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            padding: 6px;
            font-weight: bold;
        }}
        QTableView {{
            background-color: {cls.BG_PRIMARY.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            gridline-color: {cls.BORDER.name()};
            outline: none;
            alternate-background-color: {cls.TABLE_ROW_ODD.name()};
        }}
        QTableView::item {{
            padding: 5px 12px;
        }}
        QTableView::item:selected {{
            background-color: {cls.TABLE_SELECTION.name()};
            border-radius: 4px;
        }}
        QTabWidget::pane {{
            background-color: {cls.BG_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            border-top: none;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {cls.TEXT_MUTED.name()};
            border: none;
            border-bottom: 1px solid transparent;
            padding: 8px 18px;
            margin-right: 2px;
            font-size: 13px;
        }}
        QTabBar::tab:hover {{
            color: {cls.TEXT_PRIMARY.name()};
            background-color: {cls.BG_SURFACE.name()};
            border-bottom: 2px solid {cls.ACCENT.name()}60;
            border-radius: 4px 4px 0 0;
        }}
        QTabBar::tab:selected {{
            background-color: {cls.BG_PRIMARY.name()};
            color: {cls.ACCENT.name()};
            border-bottom: 2px solid {cls.ACCENT.name()};
            border-radius: 4px 4px 0 0;
            font-weight: bold;
        }}
        QLineEdit {{
            background-color: {cls.BG_SURFACE.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            border-radius: 5px;
            padding: 6px 10px;
            selection-background-color: {cls.ACCENT.name()};
            selection-color: {cls.BG_PRIMARY.name()};
        }}
        QLineEdit:focus {{
            border: 2px solid {cls.ACCENT.name()};
            background-color: {cls.BG_TERTIARY.name()};
        }}
        QLineEdit::placeholder {{
            color: {cls.TEXT_MUTED.name()};
            font-style: italic;
        }}
        QPushButton {{
            background-color: transparent;
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            border-radius: 5px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{
            background-color: {cls.BG_SURFACE.name()};
            border-color: {cls.ACCENT.name()};
        }}
        QPushButton:pressed {{
            background-color: {cls.BG_TERTIARY.name()};
            border-color: {cls.ACCENT.name()};
        }}
        QPushButton:disabled {{
            color: {cls.TEXT_MUTED.name()};
            background-color: {cls.BG_SECONDARY.name()};
            border-color: {cls.BORDER.name()};
        }}
        QPushButton[class="primary"] {{
            background-color: {cls.ACCENT.name()};
            color: #ffffff;
            border: 1px solid {cls.ACCENT.name()};
            border-radius: 5px;
            padding: 6px 20px;
            font-weight: bold;
        }}
        QPushButton[class="primary"]:hover {{
            background-color: {cls.ACCENT_PURPLE.name()};
            border-color: {cls.ACCENT_PURPLE.name()};
        }}
        QPushButton[class="primary"]:pressed {{
            background-color: {cls.ACCENT.name()};
            border-color: {cls.ACCENT.name()};
        }}
        QPushButton[class="primary"]:disabled {{
            background-color: {cls.BG_SURFACE.name()};
            color: {cls.TEXT_MUTED.name()};
            border-color: {cls.BORDER.name()};
        }}
        QSplitter::handle {{
            background-color: {cls.BORDER.name()};
            width: 2px;
            margin: 1px 0;
        }}
        QSplitter::handle:hover {{
            background-color: {cls.ACCENT.name()};
        }}
        QScrollBar:vertical {{
            background-color: transparent;
            width: 6px;
            border: none;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {cls.SCROLLBAR_FG.name()};
            min-height: 30px;
            border-radius: 3px;
            margin: 1px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.ACCENT.name()};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 6px;
            border: none;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {cls.SCROLLBAR_FG.name()};
            min-width: 30px;
            border-radius: 3px;
            margin: 1px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {cls.ACCENT.name()};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QLabel {{
            background-color: transparent;
        }}
        QGroupBox {{
            border: 1px solid {cls.BORDER.name()};
            border-radius: 6px;
            margin-top: 14px;
            padding: 12px;
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {cls.EDITOR_BG.name()};
            color: {cls.EDITOR_TEXT.name()};
            border: 1px solid {cls.BORDER.name()};
            font-family: 'Consolas', 'Cascadia Code', 'Noto Sans Thai', monospace;
        }}
        QComboBox {{
            background-color: {cls.BG_SURFACE.name()};
            color: {cls.TEXT_PRIMARY.name()};
            border: 1px solid {cls.BORDER.name()};
            border-radius: 5px;
            padding: 6px 10px;
            selection-background-color: {cls.ACCENT.name()};
            selection-color: {cls.BG_PRIMARY.name()};
        }}
        QComboBox:focus {{
            border: 1px solid {cls.ACCENT.name()};
            background-color: {cls.BG_TERTIARY.name()};
        }}
        QComboBox::drop-down {{
            border: none;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {cls.TEXT_PRIMARY.name()};
            margin-right: 4px;
        }}
        QComboBox:hover {{
            border-color: {cls.ACCENT.name()};
        }}
        QProgressBar {{
            background-color: {cls.BG_SURFACE.name()};
            border: 1px solid {cls.BORDER.name()};
            border-radius: 4px;
            text-align: center;
            color: {cls.TEXT_PRIMARY.name()};
            height: 10px;
            font-size: 11px;
        }}
        QProgressBar::chunk {{
            background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 {cls.ACCENT.name()}, stop: 1 {cls.ACCENT_GREEN.name()});
            border-radius: 3px;
        }}
        QCheckBox {{
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
        }}
        QListWidget {{
            background-color: {cls.BG_SECONDARY.name()};
            border: 1px solid {cls.BORDER.name()};
        }}
        QListWidget::item:selected {{
            background-color: {cls.TABLE_SELECTION.name()};
        }}
        QDialog {{
            background-color: {cls.BG_PRIMARY.name()};
        }}
        """


class LightTheme:
    """Light theme color scheme."""
    # (defined similarly but with light colors)
    BG_PRIMARY = QColor("#ffffff")
    BG_SECONDARY = QColor("#f5f5f5")
    BG_TERTIARY = QColor("#e8e8e8")
    BG_SURFACE = QColor("#fafafa")

    TEXT_PRIMARY = QColor("#2c3e50")
    TEXT_SECONDARY = QColor("#7f8c8d")
    TEXT_MUTED = QColor("#bdc3c7")

    ACCENT = QColor("#3498db")
    ACCENT_GREEN = QColor("#27ae60")
    ACCENT_RED = QColor("#e74c3c")
    ACCENT_YELLOW = QColor("#f39c12")
    ACCENT_ORANGE = QColor("#e67e22")
    ACCENT_PURPLE = QColor("#8e44ad")

    BORDER = QColor("#dcdcdc")

    TABLE_ROW_EVEN = QColor("#ffffff")
    TABLE_ROW_ODD = QColor("#f5f5f5")
    TABLE_SELECTION = QColor("#d5e8f5")
    TABLE_HEADER = QColor("#e8e8e8")

    SCROLLBAR_BG = QColor("#f0f0f0")
    SCROLLBAR_FG = QColor("#c0c0c0")

    EDITOR_BG = QColor("#fafafa")
    EDITOR_TEXT = QColor("#2c3e50")
    EDITOR_LINE_NUM = QColor("#bdc3c7")
    EDITOR_CURSOR = QColor("#2c3e50")

    STATUS_BG = QColor("#f0f0f0")

    @classmethod
    def stylesheet(cls) -> str:
        # Light theme stylesheet — same structure but light colors
        # (omitted for brevity; DarkTheme is the default)
        return DarkTheme.stylesheet()  # fallback; override with light colors


def coverage_color(pct: float) -> QColor:
    """Return a color based on coverage percentage."""
    if pct >= 100.0:
        return Colors.COVERAGE_COMPLETE
    elif pct >= 50.0:
        return Colors.COVERAGE_HIGH
    elif pct > 0.0:
        return Colors.COVERAGE_LOW
    return Colors.COVERAGE_NONE
