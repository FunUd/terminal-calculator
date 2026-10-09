"""Textual UI Application for Terminal Calculator."""

from __future__ import annotations
from typing import Optional, Union

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from textual.widgets import Header, Footer, Input, Static, OptionList
from textual.widgets.option_list import Option
from textual import events

from calc.config import Config
from calc.copy_screen import CopyScreen
from calc.evaluator import Evaluator, AngleMode, EvaluationError
from calc.formatter import format_result, format_bit_grid, FormatResult
from calc.help_screen import HelpScreen
from calc.highlighter import SyntaxHighlighter
from calc.history import HistoryManager
from calc.parser import ParseError


class HistoryAwareInput(Input):
    """Input widget that handles Up/Down arrows for history navigation."""

    def __init__(self, *args, **kwargs):
        if "highlighter" not in kwargs:
            kwargs["highlighter"] = SyntaxHighlighter()
        super().__init__(*args, **kwargs)
        self.app_ref: Optional[CalculatorApp] = None

    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            if self.app_ref:
                self.app_ref.action_history_up()
                event.prevent_default()
                event.stop()
        elif event.key == "down":
            if self.app_ref:
                self.app_ref.action_history_down()
                event.prevent_default()
                event.stop()
        elif event.key == "alt+a":
            if self.app_ref:
                self.app_ref.action_insert_ans_value()
                event.prevent_default()
                event.stop()
        else:
            for digit in "123456789":
                if event.key == f"alt+{digit}":
                    if self.app_ref:
                        self.app_ref.action_insert_history_value(int(digit))
                        event.prevent_default()
                        event.stop()
                    break


class CalculatorApp(App):
    """TUI Calculator Application."""

    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }

    #status-bar {
        dock: top;
        height: 1;
        background: $primary-background;
        color: $accent;
        padding: 0 1;
        text-style: bold;
    }

    #content-container {
        padding: 1 2;
        height: 1fr;
        width: 100%;
    }

    #left-pane {
        width: 55%;
        height: 1fr;
        padding-right: 1;
    }

    #right-pane {
        width: 45%;
        height: 1fr;
        padding-left: 1;
    }

    .section-title {
        text-style: bold;
        color: $primary;
        margin-top: 1;
        margin-bottom: 0;
    }

    #expr-input {
        margin-bottom: 1;
    }

    #results-container {
        border: round $primary;
        padding: 1 2;
        height: auto;
        min-height: 10;
        margin-bottom: 1;
        background: $panel;
    }

    .result-row {
        height: 1;
    }

    .result-label {
        width: 14;
        text-style: bold;
        color: $secondary;
    }

    .result-val {
        color: $text;
    }

    #warning-box {
        color: $warning;
        text-style: bold italic;
        height: auto;
        margin-top: 1;
        min-height: 1;
    }

    #error-box {
        color: $error;
        text-style: bold;
        height: auto;
        min-height: 1;
    }

    #history-container {
        height: 1fr;
        min-height: 5;
        border: round $secondary;
        padding: 0 1;
        margin-bottom: 1;
    }

    #history-list {
        height: 1fr;
        background: transparent;
    }

    #bit-grid-container {
        border: round $secondary;
        padding: 0 1;
        background: $panel;
        height: auto;
        min-height: 6;
        margin-bottom: 1;
    }

    #bit-grid-text {
        color: $accent;
        text-style: bold;
    }

    #help-box {
        border: round $primary-background;
        padding: 0 1;
        background: $panel;
        height: auto;
        min-height: 4;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("f1", "show_help", "Help"),
        Binding("question_mark", "show_help", "Help"),
        Binding("f2", "toggle_angle_mode", "DEG/RAD"),
        Binding("f3", "toggle_theme", "Theme"),
        Binding("f4", "show_copy", "Copy"),
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("escape", "clear_input", "Clear"),
        Binding("ctrl+l", "clear_input", "Clear"),
    ]

    angle_mode: reactive[AngleMode] = reactive(AngleMode.DEG, init=False)
    current_result: reactive[Optional[FormatResult]] = reactive(None, init=False)
    current_error: reactive[str] = reactive("", init=False)

    # Available Textual themes (use available_themes from Textual)
    # THEMES will be populated at runtime based on available_themes
    THEMES: list[str] = []

    def __init__(self, config: Optional[Config] = None):
        super().__init__()
        self.config = config or Config.load()
        self.angle_mode = self.config.angle_mode
        self.history_mgr = HistoryManager(max_size=self.config.max_history)
        self.evaluator = Evaluator(angle_mode=self.angle_mode)
        self._theme_index = 0
        # THEMES will be initialized in on_mount when available_themes is available

    def compose(self) -> ComposeResult:
        yield Static(id="status-bar")
        with Horizontal(id="content-container"):
            # Left pane: Expression and Calculation Results
            with Vertical(id="left-pane"):
                yield Static("Expression", classes="section-title")
                expr_input = HistoryAwareInput(
                    placeholder="Enter expression (e.g. 0xFF + 10, ans * 2, sqrt(16))...",
                    id="expr-input",
                )
                expr_input.app_ref = self
                yield expr_input

                yield Static("Results & Base Representation", classes="section-title")
                with Vertical(id="results-container"):
                    with Horizontal(classes="result-row"):
                        yield Static("DEC", classes="result-label")
                        yield Static("-", id="val-dec", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("HEX", classes="result-label")
                        yield Static("-", id="val-hex", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("BIN", classes="result-label")
                        yield Static("-", id="val-bin", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("OCT", classes="result-label")
                        yield Static("-", id="val-oct", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("Signed 16", classes="result-label")
                        yield Static("-", id="val-signed-16", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("Unsigned 16", classes="result-label")
                        yield Static("-", id="val-unsigned-16", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("Signed 32", classes="result-label")
                        yield Static("-", id="val-signed-32", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("Unsigned 32", classes="result-label")
                        yield Static("-", id="val-unsigned-32", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("Signed 64", classes="result-label")
                        yield Static("-", id="val-signed-64", classes="result-val")
                    with Horizontal(classes="result-row"):
                        yield Static("Unsigned 64", classes="result-label")
                        yield Static("-", id="val-unsigned-64", classes="result-val")

                    yield Static("", id="warning-box")
                    yield Static("", id="error-box")

            # Right pane: History, 32-bit Visualizer, Quick Reference
            with Vertical(id="right-pane"):
                yield Static("History (#1, #2... / Click or Enter to load)", classes="section-title")
                with Vertical(id="history-container"):
                    yield OptionList(id="history-list")

                yield Static("64-bit Bitfield Visualizer", classes="section-title")
                with Vertical(id="bit-grid-container"):
                    yield Static("\n".join(format_bit_grid(None)), id="bit-grid-text")

                yield Static("Quick Reference (F1: 詳細ヘルプ)", classes="section-title")
                with Vertical(id="help-box"):
                    yield Static(
                        "Vars: ans (直前) | h1..hN, $1..$N (履歴)\n"
                        "Math: sqrt(x), sin, cos, tan, log, ln, factorial\n"
                        "Bits: & (AND), | (OR), ^ (XOR), ~ (NOT), <<, >>",
                        id="help-text",
                    )

        yield Footer()

    def on_mount(self) -> None:
        # Initialize THEMES with available themes from Textual
        self.THEMES = list(self.available_themes)

        # Apply saved theme if it's available in registered themes
        if self.config.theme in self.available_themes:
            self.theme = self.config.theme
            if self.config.theme in self.THEMES:
                self._theme_index = self.THEMES.index(self.config.theme)
        self.update_status_bar()
        input_widget = self.query_one("#expr-input", HistoryAwareInput)
        input_widget.focus()

    def on_unmount(self) -> None:
        # Save configuration on exit
        self.config.angle_mode = self.angle_mode
        self.config.theme = self.theme
        self.config.save()

    def watch_angle_mode(self, new_mode: AngleMode) -> None:
        self.evaluator = Evaluator(
            angle_mode=new_mode,
            variables=self.history_mgr.get_variables(),
        )
        try:
            self.update_status_bar()
            self.calculate_current_expression()
        except Exception:
            pass

    def update_status_bar(self) -> None:
        try:
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update(f"Calc    Mode: {self.angle_mode.name} | Theme: {self.theme} | 32-bit | Ready")
        except Exception:
            pass

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_show_copy(self) -> None:
        if self.current_result:
            self.push_screen(CopyScreen(self.current_result))
        else:
            self.notify("コピー可能な結果がありません", title="クリップボード", severity="warning")

    def action_toggle_angle_mode(self) -> None:
        if self.angle_mode == AngleMode.DEG:
            self.angle_mode = AngleMode.RAD
        else:
            self.angle_mode = AngleMode.DEG

    def action_toggle_theme(self) -> None:
        """Cycle through available themes."""
        if not self.THEMES:
            self.notify("No themes available", title="Theme Error", severity="error")
            return

        self._theme_index = (self._theme_index + 1) % len(self.THEMES)
        new_theme = self.THEMES[self._theme_index]
        self.theme = new_theme
        self.notify(f"Theme: {new_theme}", title="Theme Changed")

    def action_clear_input(self) -> None:
        input_widget = self.query_one("#expr-input", HistoryAwareInput)
        input_widget.value = ""
        self.history_mgr.reset_navigation()
        self.calculate_current_expression()

    def action_history_up(self) -> None:
        input_widget = self.query_one("#expr-input", HistoryAwareInput)
        prev_expr = self.history_mgr.get_previous(input_widget.value)
        if prev_expr is not None:
            input_widget.value = prev_expr
            input_widget.cursor_position = len(prev_expr)

    def action_history_down(self) -> None:
        input_widget = self.query_one("#expr-input", HistoryAwareInput)
        next_expr = self.history_mgr.get_next()
        if next_expr is not None:
            input_widget.value = next_expr
            input_widget.cursor_position = len(next_expr)

    def action_insert_history_value(self, n: int) -> None:
        """Insert result_repr of the n-th oldest history item (1-based) at the cursor.

        Uses list-index position so Alt+1 always reaches the oldest surviving entry
        and Alt+9 always reaches the 9th oldest, regardless of overflow or dedup.
        """
        if n < 1 or n > len(self.history_mgr.items):
            return
        item = self.history_mgr.items[n - 1]
        input_widget = self.query_one("#expr-input", HistoryAwareInput)
        input_widget.insert_text_at_cursor(item.result_repr)

    def action_insert_ans_value(self) -> None:
        """Insert the most recent result (ans) at the current cursor position."""
        if not self.history_mgr.items:
            return
        input_widget = self.query_one("#expr-input", HistoryAwareInput)
        input_widget.insert_text_at_cursor(self.history_mgr.items[-1].result_repr)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "expr-input":
            self.calculate_current_expression()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "expr-input":
            expr = event.value.strip()
            if not expr:
                return

            try:
                val = self.evaluator.evaluate_expr(expr)
                formatted = format_result(val)
                self.history_mgr.add(expr, formatted.dec, raw_value=val)
                self.refresh_history_ui()
                self.history_mgr.reset_navigation()
            except (ParseError, EvaluationError):
                # Don't add invalid expression to history
                pass

    def calculate_current_expression(self) -> None:
        try:
            input_widget = self.query_one("#expr-input", HistoryAwareInput)
        except Exception:
            return

        expr = input_widget.value.strip()

        if not expr:
            self.clear_display()
            return

        try:
            self.evaluator.variables = self.history_mgr.get_variables()
            val = self.evaluator.evaluate_expr(expr)
            formatted = format_result(val)
            self.current_result = formatted
            self.display_result(formatted)
            self.query_one("#error-box", Static).update("")
        except (ParseError, EvaluationError) as e:
            # Display gentle error without crashing
            self.clear_display(keep_error=True)
            self.query_one("#error-box", Static).update(f"Error: {e}")

    def display_result(self, res: FormatResult) -> None:
        self.query_one("#val-dec", Static).update(res.dec)
        self.query_one("#val-hex", Static).update(res.hex)
        self.query_one("#val-bin", Static).update(res.bin)
        self.query_one("#val-oct", Static).update(res.oct)
        self.query_one("#val-signed-16", Static).update(
            str(res.signed_16) if res.signed_16 is not None else "N/A"
        )
        self.query_one("#val-unsigned-16", Static).update(
            str(res.unsigned_16) if res.unsigned_16 is not None else "N/A"
        )
        self.query_one("#val-signed-32", Static).update(
            str(res.signed_32) if res.signed_32 is not None else "N/A"
        )
        self.query_one("#val-unsigned-32", Static).update(
            str(res.unsigned_32) if res.unsigned_32 is not None else "N/A"
        )
        self.query_one("#val-signed-64", Static).update(
            str(res.signed_64) if res.signed_64 is not None else "N/A"
        )
        self.query_one("#val-unsigned-64", Static).update(
            str(res.unsigned_64) if res.unsigned_64 is not None else "N/A"
        )
        self.query_one("#warning-box", Static).update(res.warning)

        # Update 64-bit bitfield visualizer
        bit_val = int(res.dec) if res.is_integer else None
        self.query_one("#bit-grid-text", Static).update("\n".join(format_bit_grid(bit_val)))

    def clear_display(self, keep_error: bool = False) -> None:
        self.current_result = None
        self.query_one("#val-dec", Static).update("-")
        self.query_one("#val-hex", Static).update("-")
        self.query_one("#val-bin", Static).update("-")
        self.query_one("#val-oct", Static).update("-")
        self.query_one("#val-signed-16", Static).update("-")
        self.query_one("#val-unsigned-16", Static).update("-")
        self.query_one("#val-signed-32", Static).update("-")
        self.query_one("#val-unsigned-32", Static).update("-")
        self.query_one("#val-signed-64", Static).update("-")
        self.query_one("#val-unsigned-64", Static).update("-")
        self.query_one("#warning-box", Static).update("")
        self.query_one("#bit-grid-text", Static).update("\n".join(format_bit_grid(None)))
        if not keep_error:
            self.query_one("#error-box", Static).update("")

    def refresh_history_ui(self) -> None:
        opt_list = self.query_one("#history-list", OptionList)
        opt_list.clear_options()
        items = self.history_mgr.items
        total = len(items)
        # Display newest first; label by 1-based list position so
        # panel label N always matches Alt+N insertion semantics.
        for display_pos, item in enumerate(reversed(items)):
            list_index = total - display_pos   # newest item = total, oldest = 1
            opt_list.add_option(
                Option(f"#{list_index:<2} {item.expr:<20} = {item.result_repr}", id=item.expr)
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id:
            input_widget = self.query_one("#expr-input", HistoryAwareInput)
            input_widget.value = event.option_id
            input_widget.focus()
            input_widget.cursor_position = len(event.option_id)


def main() -> None:
    app = CalculatorApp()
    app.run()


if __name__ == "__main__":
    main()
