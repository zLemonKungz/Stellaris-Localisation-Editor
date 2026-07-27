"""
Text editor panel with Stellaris syntax highlighting for localisation values.

Highlights:
  - $VARIABLE$     → orange (variable placeholder)
  - £icon£         → purple (inline icon)
  - §R...§!        → red (red color tag)
  - §G...§!        → green (green color tag)
  - §Y...§!        → yellow (yellow color tag)
  - §H...§!        → cyan (highlight color tag)
  - §L...§!        → gray (lore color tag)
  - §!             → dim (color close)
  - $KEY$          → blue (cross-reference to another key)
"""

import re

from PyQt6.QtCore import Qt, QRect, QRegularExpression, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import (
    QColor, QSyntaxHighlighter, QTextCharFormat, QFont,
    QPainter, QTextCursor, QKeySequence, QTextFormat,
)
from PyQt6.QtWidgets import (
    QWidget, QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QToolTip, QTextEdit,
)

from .themes import DarkTheme, Colors
from ..core.spell_check import SpellChecker
from ..core.suggestion import SuggestionEngine


# ── Stellaris Syntax Highlighter ──────────────────────────────────────────

class StellarisHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for Stellaris localisation text.
    Applies color formatting to variables, icons, color tags, and key refs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Format for $VARIABLE$ (variables)
        self.var_format = QTextCharFormat()
        self.var_format.setForeground(Colors.SYNTAX_VARIABLE)
        self.var_format.setFontWeight(QFont.Weight.Bold)

        # Format for £icon£ (icons)
        self.icon_format = QTextCharFormat()
        self.icon_format.setForeground(Colors.SYNTAX_ICON)
        self.icon_format.setFontWeight(QFont.Weight.Bold)

        # Format for color tag content
        self.color_tag_format = QTextCharFormat()
        self.color_tag_format.setFontWeight(QFont.Weight.Bold)

        # Sub-formats per color
        self.tag_formats = {
            'R': QTextCharFormat(),
            'G': QTextCharFormat(),
            'Y': QTextCharFormat(),
            'H': QTextCharFormat(),
            'L': QTextCharFormat(),
        }
        colors = {
            'R': Colors.SYNTAX_COLOR_TAG_R,
            'G': Colors.SYNTAX_COLOR_TAG_G,
            'Y': Colors.SYNTAX_COLOR_TAG_Y,
            'H': Colors.SYNTAX_COLOR_TAG_H,
            'L': Colors.SYNTAX_COLOR_TAG_L,
        }
        for letter, color in colors.items():
            fmt = self.tag_formats[letter]
            fmt.setForeground(color)
            fmt.setFontWeight(QFont.Weight.Bold)

        # Format for $KEY$ cross-references
        self.key_ref_format = QTextCharFormat()
        self.key_ref_format.setForeground(Colors.SYNTAX_ICON)
        self.key_ref_format.setFontItalic(True)

        # Color close §!
        self.color_close_format = QTextCharFormat()
        self.color_close_format.setForeground(QColor("#555555"))

    def highlightBlock(self, text: str):
        """Apply highlighting to the given text block."""

        # 1. Highlight §X...§! color regions (process first so nested rules
        #    can still apply after color tag closes — but we process them
        #    in the correct order so color tags take visual priority)

        # First pass: find all color tag boundaries
        color_regions = []  # (start, end, format)
        i = 0
        while i < len(text):
            # Check for §X opening (X is R, G, Y, H, L)
            if text[i] == '§' and i + 1 < len(text):
                letter = text[i + 1]
                if letter in self.tag_formats:
                    start = i
                    # Find closing §!
                    close_pos = text.find('§!', i + 2)
                    if close_pos >= 0:
                        end = close_pos + 2
                        color_regions.append(
                            (start, end, self.tag_formats[letter])
                        )
                        i = end
                        continue
                    else:
                        # No closing tag — highlight from §X to end
                        color_regions.append(
                            (start, len(text), self.tag_formats[letter])
                        )
                        break
                elif letter == '!':
                    # Color close §!
                    self.setFormat(i, 2, self.color_close_format)
                    i += 2
                    continue
                elif letter == '_':
                    # §_...§! — reset/plain, skip highlighting
                    close_pos = text.find('§!', i + 2)
                    if close_pos >= 0:
                        i = close_pos + 2
                    else:
                        i += 2
                    continue
            i += 1

        # Apply color region formats first (they have visual priority)
        for start, end, fmt in color_regions:
            self.setFormat(start, end - start, fmt)

        # 2. Highlight $VARIABLE$ patterns (including $KEY|F$ with pipe)
        var_pattern = re.compile(r'\$[A-Za-z_][A-Za-z0-9_]*(?:\|[A-Za-z0-9_]+)?\$')
        for match in var_pattern.finditer(text):
            start, end = match.start(), match.end()
            # Don't override color tag regions
            if not self._in_region(start, color_regions):
                self.setFormat(start, end - start, self.var_format)

        # 3. Highlight £icon£ patterns
        icon_pattern = re.compile(r'£[a-z_][a-z0-9_]*£')
        for match in icon_pattern.finditer(text):
            start, end = match.start(), match.end()
            if not self._in_region(start, color_regions):
                self.setFormat(start, end - start, self.icon_format)

    def _in_region(self, pos: int, regions: list[tuple]) -> bool:
        """Check if position is within any of the given ranges."""
        for start, end, _ in regions:
            if start <= pos < end:
                return True
        return False


# ── Line Number Area ──────────────────────────────────────────────────────

class LineNumberArea(QWidget):
    """Widget painted alongside the text edit for line numbers."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor._line_number_area_paint_event(event)


class LineNumberTextEdit(QPlainTextEdit):
    """QPlainTextEdit with line number gutter and current-line highlight."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self._user_extra_selections = []
        self._current_line_selection = None

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._on_cursor_moved)

        self._update_line_number_area_width(0)
        # QTimer.singleShot ensures layout is ready before first highlight
        from PyQt6.QtCore import QTimer as _QTimer
        _QTimer.singleShot(0, self._on_cursor_moved)

    # ── Extra selections: merge user spell selections + current line ──

    def setExtraSelections(self, selections):
        """Override: store user selections; always inject current-line highlight."""
        self._user_extra_selections = list(selections)
        self._apply_extra_selections()

    def _apply_extra_selections(self):
        all_sel = list(self._user_extra_selections)
        if self._current_line_selection:
            all_sel.insert(0, self._current_line_selection)
        # Call the REAL QPlainTextEdit.setExtraSelections, not our override
        QPlainTextEdit.setExtraSelections(self, all_sel)

    def _on_cursor_moved(self):
        """Rebuild and re-apply current-line highlight selection."""
        sel = QTextEdit.ExtraSelection()
        # Very subtle highlight using table selection color at low alpha
        line_color = QColor(DarkTheme.ACCENT)
        line_color.setAlpha(22)
        sel.format.setBackground(line_color)
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self._current_line_selection = sel
        self._apply_extra_selections()

    # ── Line number gutter ──

    def _line_number_area_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 12 + self.fontMetrics().horizontalAdvance('9') * digits

    def _update_line_number_area_width(self, _new_block_count=None):
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            area = self._line_number_area
            area.update(0, rect.y(), area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )

    def _line_number_area_paint_event(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), DarkTheme.BG_SECONDARY)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        block_geo = self.blockBoundingGeometry(block).translated(self.contentOffset())
        top = int(block_geo.top())
        bottom = int(top + self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(DarkTheme.EDITOR_LINE_NUM)
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 6, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number,
                )
            block = block.next()
            block_geo = self.blockBoundingGeometry(block).translated(self.contentOffset())
            top = int(block_geo.top())
            bottom = int(top + self.blockBoundingRect(block).height())
            block_number += 1


# ── Editor Panel ──────────────────────────────────────────────────────────

class EditorPanel(QWidget):
    """
    Editor panel for viewing and editing a single translation value.
    Shows the key name, the current value with syntax highlighting,
    provides search/replace, validation warnings, value stats,
    **spell checking** (red wavy lines under misspelled words),
    and **translation suggestions** (glossary + translation memory).
    """

    value_saved = pyqtSignal(str, str)  # key, new_value
    navigate_prev = pyqtSignal()  # navigate to previous untranslated
    navigate_next = pyqtSignal()  # navigate to next untranslated

    def __init__(self, spell_checker=None, suggestion_engine=None, parent=None):
        super().__init__(parent)
        self.spell_checker = spell_checker
        self.suggestion_engine = suggestion_engine
        self._current_key: str = ""
        self._current_file: str = ""
        self._original_value: str = ""
        self._has_changes = False
        self._spell_errors: list = []
        self._spell_dirty = False
        self._setup_ui()
        self._setup_spell_timer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # ── Header: key name + navigation + char count ──
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        self.key_label = QLabel("No key selected")
        self.key_label.setStyleSheet(f"""
            font-size: 14px; font-weight: bold;
            color: {DarkTheme.ACCENT.name()};
            padding: 2px 0;
        """)
        header_layout.addWidget(self.key_label, 1)

        # Copy key name button
        self.copy_key_btn = QPushButton("📋 Copy")
        self.copy_key_btn.setFixedSize(50, 22)
        self.copy_key_btn.setToolTip("Copy key name to clipboard")
        self.copy_key_btn.clicked.connect(self._copy_key_name)
        self.copy_key_btn.setStyleSheet("font-size: 10px; padding: 1px 4px;")
        header_layout.addWidget(self.copy_key_btn)

        # Navigation buttons
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setFixedSize(60, 22)
        self.prev_btn.setToolTip("Previous untranslated key")
        self.prev_btn.clicked.connect(self.navigate_prev.emit)
        self.prev_btn.setStyleSheet("font-size: 10px; padding: 1px 4px;")
        header_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedSize(60, 22)
        self.next_btn.setToolTip("Next untranslated key")
        self.next_btn.clicked.connect(self.navigate_next.emit)
        self.next_btn.setStyleSheet("font-size: 10px; padding: 1px 4px;")
        header_layout.addWidget(self.next_btn)

        self.char_count = QLabel("")
        self.char_count.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()};
            font-size: 11px; padding: 2px 4px;
        """)
        header_layout.addWidget(self.char_count)

        layout.addLayout(header_layout)

        # ── Toolbar ──
        edit_toolbar = QHBoxLayout()
        edit_toolbar.setSpacing(4)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Find in value...")
        self.search_edit.textChanged.connect(self._search_in_editor)
        edit_toolbar.addWidget(self.search_edit, 1)

        edit_toolbar.addStretch()

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.clicked.connect(self._reset_value)
        self.reset_btn.setToolTip("Reset to original value")
        edit_toolbar.addWidget(self.reset_btn)

        self.save_value_btn = QPushButton("💾 Apply")
        self.save_value_btn.clicked.connect(self._save_value)
        self.save_value_btn.setEnabled(False)
        self.save_value_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {DarkTheme.ACCENT.name()};
                color: {DarkTheme.BG_PRIMARY.name()};
                font-weight: bold;
            }}
            QPushButton:disabled {{
                background-color: {DarkTheme.BG_SURFACE.name()};
                color: {DarkTheme.TEXT_MUTED.name()};
            }}
        """)
        edit_toolbar.addWidget(self.save_value_btn)

        layout.addLayout(edit_toolbar)

        # ── Editor (with line numbers and current-line highlight) ──
        self.editor = LineNumberTextEdit()
        self.editor.setMinimumHeight(100)
        self.editor.setMaximumHeight(220)
        self.editor.setTabStopDistance(24)
        self.editor.setPlaceholderText("Select a key to edit its translation value...")
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        # Custom context menu for spelling suggestions
        self.editor.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.editor.customContextMenuRequested.connect(
            self._show_spelling_menu
        )

        # Install syntax highlighter
        self.highlighter = StellarisHighlighter(self.editor.document())

        layout.addWidget(self.editor)

        # ── Validation warnings (compact badge) ──
        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(False)
        self.warning_label.setStyleSheet(f"""
            color: {DarkTheme.ACCENT_RED.name()};
            font-size: 10px;
            font-weight: bold;
            padding: 1px 8px;
            background-color: rgba(243, 139, 168, 0.12);
            border-radius: 4px;
            border: 1px solid rgba(243, 139, 168, 0.3);
            min-height: 14px;
            max-height: 18px;
        """)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # ── Tag insertion buttons (compact) ──
        ref_line = QHBoxLayout()
        ref_line.setSpacing(2)
        ref_label = QLabel("Insert:")
        ref_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()};
            font-size: 9px;
            padding: 0;
        """)
        ref_line.addWidget(ref_label)

        for tag, tip, color in [
            ("$VAR$", "Game variable", Colors.SYNTAX_VARIABLE),
            ("£icon£", "Game icon", Colors.SYNTAX_ICON),
            ("§R", "Red text", Colors.SYNTAX_COLOR_TAG_R),
            ("§G", "Green text", Colors.SYNTAX_COLOR_TAG_G),
            ("§Y", "Yellow text", Colors.SYNTAX_COLOR_TAG_Y),
            ("§H", "Highlight", Colors.SYNTAX_COLOR_TAG_H),
            ("§L", "Lore text", Colors.SYNTAX_COLOR_TAG_L),
            ("§!", "Close color", QColor("#888888")),
        ]:
            btn = QPushButton(tag)
            btn.setFixedHeight(16)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda checked, t=tag: self._insert_template(t))
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-family: 'Consolas', monospace;
                    font-size: 9px;
                    padding: 0 3px;
                    color: {color.name()};
                    background-color: {DarkTheme.BG_SURFACE.name()};
                    border: 1px solid {DarkTheme.BORDER.name()};
                    border-radius: 2px;
                }}
                QPushButton:hover {{
                    background-color: {DarkTheme.BORDER.name()};
                }}
            """)
            ref_line.addWidget(btn)

        ref_line.addStretch()
        layout.addLayout(ref_line)

        # ── Status label (key + stats, inline) ──
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(False)
        self.status_label.setStyleSheet(f"""
            color: {DarkTheme.TEXT_MUTED.name()};
            font-size: 10px;
            padding: 1px 4px;
            font-family: 'Consolas', 'Segoe UI', monospace;
        """)
        layout.addWidget(self.status_label)

    def set_value(self, key: str, value: str, filename: str = ""):
        """Set the key and value to edit."""
        self._current_key = key
        self._current_file = filename
        self._original_value = value
        self._has_changes = False

        self.key_label.setText(f"🔑 {key}")
        self.editor.setPlainText(value)
        self._update_stats_and_warnings()
        self._clear_spell_errors()
        self.save_value_btn.setEnabled(False)
        self.status_label.setText(
            f"Editing key in {filename}" if filename else "Editing key"
        )

    def clear(self):
        """Clear the editor."""
        self._current_key = ""
        self._current_file = ""
        self._original_value = ""
        self._has_changes = False
        self.key_label.setText("No key selected")
        self.editor.clear()
        self.char_count.setText("")
        self.warning_label.hide()
        self._clear_spell_errors()
        self.save_value_btn.setEnabled(False)
        self.status_label.setText("Ready")

    def _on_text_changed(self):
        try:
            self._update_stats_and_warnings()
            self._mark_spell_dirty()
            if self._current_key:
                self._has_changes = True
                self.save_value_btn.setEnabled(True)
        except Exception:
            pass

    def _update_stats_and_warnings(self):
        """Update char count, status label, and validation warnings."""
        text = self.editor.toPlainText()
        if not self._current_key:
            return

        self.char_count.setText(f"{len(text)} chars")

        if not text.strip():
            self.status_label.setText("Empty value (not translated)")
            self.warning_label.hide()
            return

        # Value statistics — merged into status label
        import re
        var_count = len(re.findall(r'\$[A-Za-z0-9_|]+?\$', text))
        icon_count = len(re.findall(r'£[a-z_]+?£', text))
        color_count = len(re.findall(r'§[RGYHL]', text))

        stats = f"{len(text)}c | ${var_count} £{icon_count} §{color_count}"
        if len(text) > 500:
            stats += " LONG"
        if self._spell_errors:
            stats += f" ✗{len(self._spell_errors)}"

        if self._has_changes:
            self.status_label.setText(f"✎ {self._current_key} | {stats}")
        else:
            self.status_label.setText(f"{self._current_key} | {stats}")

        # Validation: check for common issues
        warnings = []

        # Check unclosed color tags
        open_colors = re.findall(r'§[RGYHL]', text)
        close_colors = re.findall(r'§!', text)
        if len(open_colors) > len(close_colors):
            warnings.append(
                f"⚠️ Unclosed color tag(s): {len(open_colors)}§X but "
                f"only {len(close_colors)}§!"
            )
        elif len(open_colors) < len(close_colors):
            warnings.append(
                f"⚠️ Extra §! close tag(s): {len(close_colors)}§! but "
                f"only {len(open_colors)}§X"
            )

        # Check unclosed $ variables
        open_vars = len(re.findall(r'\$[A-Za-z0-9_|]+?[^$]', text))
        actual_vars = len(re.findall(r'\$[A-Za-z0-9_|]+?\$', text))
        # Count $ signs
        dollar_count = text.count('$')
        if dollar_count % 2 != 0:
            warnings.append("⚠️ Unclosed $VAR$ (odd number of $ signs)")

        # Check unclosed £ icons
        pound_count = text.count('£')
        if pound_count % 2 != 0:
            warnings.append("⚠️ Unclosed £icon£ (odd number of £ signs)")

        if warnings:
            count = len(warnings)
            self.warning_label.setText(f"⚠️ {count} issue{'s' if count != 1 else ''}")
            self.warning_label.setToolTip("\n".join(f"• {w}" for w in warnings))
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def _save_value(self):
        try:
            if self._current_key and self._has_changes:
                new_value = self.editor.toPlainText()
                self.value_saved.emit(self._current_key, new_value)
                self._has_changes = False
                self.save_value_btn.setEnabled(False)
                self._clear_spell_errors()
                self._update_stats_and_warnings()
                self.status_label.setText(f"✓ Saved: {self._current_key}")
        except Exception as exc:
            self.status_label.setText(f"Error saving: {exc}")

    def _reset_value(self):
        """Reset editor to the original value."""
        if self._current_key and self._original_value is not None:
            was_changed = self._has_changes
            self.editor.setPlainText(self._original_value)
            self._has_changes = False
            self.save_value_btn.setEnabled(False)
            self._clear_spell_errors()
            self._update_stats_and_warnings()
            self.status_label.setText(
                "Reset to original" if was_changed else "No changes to reset"
            )

    def _replace_word(self, old_word: str, new_word: str):
        """Replace a misspelled word in the editor text."""
        text = self.editor.toPlainText()
        # Replace only the first occurrence
        idx = text.find(old_word)
        if idx >= 0:
            new_text = text[:idx] + new_word + text[idx + len(old_word):]
            self.editor.setPlainText(new_text)
            self._mark_spell_dirty()

    def _copy_key_name(self):
        """Copy current key name to clipboard."""
        if self._current_key:
            from PyQt6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(self._current_key)
            self.status_label.setText(f"📋 Copied: {self._current_key}")

    def _insert_template(self, template: str):
        """Insert a template tag at the cursor position."""
        cursor = self.editor.textCursor()
        cursor.insertText(template)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _search_in_editor(self, text: str):
        """Search for text within the editor."""
        if not text:
            cursor = self.editor.textCursor()
            cursor.clearSelection()
            self.editor.setTextCursor(cursor)
            return

        # Find and select text
        found = self.editor.find(text)
        if not found:
            # Wrap around
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            self.editor.find(text)

    # ── Spell Timer ───────────────────────────────────────────────────

    def _setup_spell_timer(self):
        """Set up a debounced timer for spell checking (2s delay)."""
        self._spell_timer = QTimer(self)
        self._spell_timer.setInterval(2000)  # 2s debounce — only check after pause
        self._spell_timer.setSingleShot(True)
        self._spell_timer.timeout.connect(self._check_spelling)

    def _mark_spell_dirty(self):
        """Mark spell check as needed and restart the debounce timer."""
        self._spell_dirty = True
        self._spell_timer.start()  # restart on each keystroke

    def _clear_spell_errors(self):
        """Clear all spell error highlights."""
        self._spell_errors = []
        self._spell_dirty = False
        self._spell_timer.stop()
        if self.spell_checker and hasattr(self.editor, 'setExtraSelections'):
            # Clear only the spell error selections by resetting
            try:
                self.editor.setExtraSelections([])
            except Exception:
                pass

    def _check_spelling(self):
        """Run spell checker (fast path — no Levenshtein) and update highlights."""
        if not self.spell_checker or not self._current_key:
            self._clear_spell_errors()
            return

        text = self.editor.toPlainText()
        if not text.strip():
            self._clear_spell_errors()
            return

        try:
            # Use FAST check — no Levenshtein, just identify errors
            self._spell_errors = self.spell_checker.check_text_fast(text)
        except Exception:
            self._spell_errors = []

        self._spell_dirty = False

        # ── Update extra selections for red wavy underlines ──
        # (current-line highlight is injected automatically by LineNumberTextEdit)
        if not self._spell_errors:
            try:
                self.editor.setExtraSelections([])
            except Exception:
                pass
        else:
            selections = []
            for err in self._spell_errors:
                cursor = self.editor.textCursor()
                cursor.setPosition(err.start)
                cursor.setPosition(err.end, QTextCursor.MoveMode.KeepAnchor)
                extra = QTextEdit.ExtraSelection()
                extra.cursor = cursor
                extra.format.setUnderlineStyle(
                    QTextCharFormat.UnderlineStyle.SpellCheckUnderline
                )
                extra.format.setUnderlineColor(QColor("#ff4444"))
                selections.append(extra)

            try:
                self.editor.setExtraSelections(selections)
            except Exception:
                pass

        # Update stats bar with error count
        self._update_stats_and_warnings()

    # ── Right-click context menu for spelling ─────────────────────────

    def _show_spelling_menu(self, pos):
        """Show right-click context menu with spelling suggestions."""
        cursor = self.editor.cursorForPosition(pos)
        cursor_pos = cursor.position()

        # Find if cursor is on a misspelled word
        target_error = None
        for err in self._spell_errors:
            if err.start <= cursor_pos <= err.end:
                target_error = err
                break

        # Create menu
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        if target_error and target_error.word:
            # Compute suggestions ON DEMAND (this is the slow Levenshtein part)
            fix_word = target_error.word
            suggestions = self.spell_checker.get_suggestions(fix_word, 5)

            menu.addSection(f"✗ \"{fix_word}\"")

            if suggestions:
                for s in suggestions:
                    act = menu.addAction(f"✓ แก้เป็น \"{s}\"")
                    act.setData(("replace", fix_word, s))
                menu.addSeparator()
                act = menu.addAction(f"➕ เพิ่ม \"{fix_word}\" ใน dictionary")
                act.setData(("ignore", fix_word, None))
            else:
                no_suggest = menu.addAction("(ไม่มีคำแนะนำ)")
                no_suggest.setEnabled(False)
                act = menu.addAction(f"➕ เพิ่ม \"{fix_word}\" ใน dictionary")
                act.setData(("ignore", fix_word, None))
        else:
            # No spelling error — add default paste/copy actions
            # (QPlainTextEdit already provides these)
            pass

        # Add glossary look-up for selected text
        selected = self.editor.textCursor().selectedText()
        if selected and hasattr(self, 'suggestion_engine') and self.suggestion_engine:
            gloss = self.suggestion_engine.get_glossary_suggestions(selected)
            if gloss:
                menu.addSeparator()
                menu.addSection(f"📖 Glossary: \"{selected}\"")
                for g in gloss:
                    act = menu.addAction(f"  → {g}")
                    act.setData(("glossary", selected, g))

        if not menu.isEmpty():
            action = menu.exec(self.editor.viewport().mapToGlobal(pos))
            if action and action.data():
                act_type, arg1, arg2 = action.data()
                if act_type == "replace":
                    self._replace_word(arg1, arg2)
                elif act_type == "glossary":
                    self._insert_template(arg2)
        else:
            # Pass through to default context menu
            default_menu = self.editor.createStandardContextMenu()
            default_menu.exec(self.editor.viewport().mapToGlobal(pos))
