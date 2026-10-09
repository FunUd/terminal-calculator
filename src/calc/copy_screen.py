"""Modal dialog to copy calculation results in various bases to clipboard."""

from __future__ import annotations
from typing import Optional

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option

from calc.clipboard import copy_to_clipboard
from calc.formatter import FormatResult


class CopyScreen(ModalScreen[Optional[str]]):
    """Modal screen for copying calculation results in different bases."""

    BINDINGS = [
        Binding("escape", "dismiss_dialog", "Cancel", priority=True),
        Binding("q", "dismiss_dialog", "Cancel", priority=True),
    ]

    CSS = """
    CopyScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #copy-dialog {
        width: 60;
        height: auto;
        max-height: 20;
        border: thick $primary;
        background: $panel;
        padding: 1 2;
    }

    #dialog-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #copy-options {
        height: auto;
        max-height: 12;
        background: transparent;
    }
    """

    def __init__(self, result: Optional[FormatResult] = None):
        super().__init__()
        self.result = result
        self.options_map: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="copy-dialog"):
            yield Static("クリップボードにコピー (数字キー 1-8 または Enter)", id="dialog-title")
            opt_list = OptionList(id="copy-options")

            if self.result is not None:
                items = [
                    ("1", "DEC", self.result.dec),
                    ("2", "HEX", self.result.hex),
                    ("3", "BIN", self.result.bin),
                    ("4", "OCT", self.result.oct),
                    ("5", "Signed 16", str(self.result.signed_16) if self.result.signed_16 is not None else "N/A"),
                    ("6", "Unsigned 16", str(self.result.unsigned_16) if self.result.unsigned_16 is not None else "N/A"),
                    ("7", "Signed 32", str(self.result.signed_32) if self.result.signed_32 is not None else "N/A"),
                    ("8", "Unsigned 32", str(self.result.unsigned_32) if self.result.unsigned_32 is not None else "N/A"),
                    ("9", "Signed 64", str(self.result.signed_64) if self.result.signed_64 is not None else "N/A"),
                    ("0", "Unsigned 64", str(self.result.unsigned_64) if self.result.unsigned_64 is not None else "N/A"),
                ]
                for num, label, val in items:
                    if val != "N/A":
                        prompt = f"[{num}] {label:<12}: {val}"
                        opt_list.add_option(Option(prompt, id=num))
                        self.options_map[num] = val
            else:
                opt_list.add_option(Option("コピー可能な結果がありません", id="none"))

            yield opt_list

    def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "q"):
            self.dismiss(None)
            event.stop()
            event.prevent_default()
            return

        # Direct number keys 1-6
        if event.key in self.options_map:
            val = self.options_map[event.key]
            self._do_copy(val)
            event.stop()
            event.prevent_default()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id and event.option_id in self.options_map:
            val = self.options_map[event.option_id]
            self._do_copy(val)

    def _do_copy(self, text: str) -> None:
        copy_to_clipboard(text, app=self.app)
        if self.app:
            self.app.notify(f"コピーしました: {text}", title="クリップボード", timeout=3.0)
        self.dismiss(text)

    def action_dismiss_dialog(self) -> None:
        self.dismiss(None)
