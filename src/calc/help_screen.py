"""Help modal screen for Terminal Calculator."""

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Static, Button


HELP_MARKDOWN = """
[bold cyan]Terminal Calculator (TUI 電卓) ヘルプ & リファレンス[/bold cyan]
[dim]Esc / Enter / q / F1 で閉じる[/dim]

[bold yellow]■ 基本キー操作[/bold yellow]
  • [bold]Enter[/bold]       : 入力中の式を確定し、履歴に追加
  • [bold]↑ / ↓[/bold]       : 入力欄で履歴を巡回呼び出し（編集ドラフトへ復帰可能）
  • [bold]F1 / ?[/bold]      : このヘルプ画面を表示
  • [bold]F2[/bold]          : 角度モード切替 (DEG ⇔ RAD)
  • [bold]F3[/bold]          : テーマ切替 (default, alabaster, catppuccin-mocha, etc.)
  • [bold]F4[/bold]          : クリップボードにコピー
  • [bold]Esc / Ctrl+L[/bold]: 入力欄をクリア
  • [bold]Ctrl+Q[/bold]      : 電卓を終了
  • [bold]Tab[/bold]         : 入力欄と履歴一覧間のフォーカス移動

[bold yellow]■ 履歴変数の利用[/bold yellow]
  • [bold cyan]ans[/bold cyan]       : 直前の計算結果 (例: [dim]ans * 2[/dim], [dim]ans + 0x10[/dim])
  • [bold cyan]h1, h2...[/bold cyan] : 履歴番号 (#1, #2...) の結果値 (例: [dim]2 + 2 + h1[/dim])
  • [bold cyan]$1, $2...[/bold cyan] : 履歴番号の別表記 (例: [dim]h1 + $2[/dim])

[bold yellow]■ 数値リテラル (混在計算可能)[/bold yellow]
  • 10進数: [cyan]123[/cyan], [cyan]1_000_000[/cyan]
  • 16進数: [cyan]0xFF[/cyan], [cyan]0x109[/cyan]
  • 2進数 : [cyan]0b1010[/cyan], [cyan]0b1111_0000[/cyan]
  • 8進数 : [cyan]0o17[/cyan], [cyan]0o77[/cyan]
  • 小数・指数: [cyan]3.14[/cyan], [cyan]1.2e-3[/cyan]

[bold yellow]■ SI 接頭辞 / 工学単位サフィックス[/bold yellow]
  • 数値の末尾にサフィックスを付けて倍率を指定できます:
    [cyan]1k[/cyan] / [cyan]1K[/cyan]  → 1,000          (キロ, ×10³)
    [cyan]1M[/cyan]      → 1,000,000      (メガ, ×10⁶)
    [cyan]1G[/cyan]      → 1,000,000,000  (ギガ, ×10⁹)
    [cyan]1m[/cyan]      → 0.001          (ミリ, ×10⁻³)
    [cyan]10u[/cyan]     → 0.00001        (マイクロ, ×10⁻⁶)
    [cyan]100n[/cyan]    → 0.0000001      (ナノ, ×10⁻⁹)
    [cyan]1p[/cyan]      → 1e-12          (ピコ, ×10⁻¹²)
  • 例: [dim]10k * 2[/dim] → [cyan]20000[/cyan]、[dim]1.5M / 100[/dim] → [cyan]15000[/cyan]
  • 小数にも使用可: [dim]2.2k[/dim] → [cyan]2200.0[/cyan]、[dim]4.7u[/dim] → [cyan]4.7e-06[/cyan]
  • [dim]m[/dim](ミリ, ×10⁻³) と [dim]M[/dim](メガ, ×10⁶) は大文字小文字で区別されます

[bold yellow]■ 演算子 (優先度順)[/bold yellow]
  1. [bold]()[/bold]           : グループ化
  2. [bold]**[/bold]           : べき乗 (右結合, 例: [dim]2 ** 3 ** 2 = 512[/dim], [dim]-2 ** 2 = -4[/dim])
  3. [bold]+, -, ~[/bold]     : 単項プラス, 単項マイナス, ビットNOT (32-bit反転)
  4. [bold]*, /, //, %[/bold] : 乗算, 除算, 整数除算, 剰余
  5. [bold]+, -[/bold]        : 加算, 減算
  6. [bold]<<, >>[/bold]      : 左シフト, 論理右シフト (シフト量 0〜31)
  7. [bold]&[/bold]            : ビットAND
  8. [bold]^[/bold]            : ビットXOR (排他的論理和)
  9. [bold]|[/bold]            : ビットOR

[bold yellow]■ 関数 & 定数[/bold yellow]
  • [bold]sqrt(x)[/bold]       : 平方根 (完全平方数は整数を返却, 例: [dim]sqrt(16) -> 4[/dim])
  • [bold]sin, cos, tan[/bold] : 三角関数 (DEG/RAD モード連動)
  • [bold]asin, acos, atan[/bold]: 逆三角関数 (DEG/RAD モード連動)
  • [bold]log(x)[/bold]        : 常用対数 (底10, 例: [dim]log(100) -> 2[/dim])
  • [bold]ln(x)[/bold]         : 自然対数 (底e, 例: [dim]ln(e) -> 1[/dim])
  • [bold]abs(x)[/bold]        : 絶対値
  • [bold]factorial(n)[/bold] : 階乗 (0 <= n <= 1000)
  • [bold]exp(x)[/bold]        : 指数関数 (e^x)
  • [bold]bswap16(x)[/bold]    : 16ビットバイトスワップ (例: [dim]bswap16(0x1234) -> 0x3412[/dim])
  • [bold]bswap32(x)[/bold]    : 32ビットバイトスワップ (例: [dim]bswap32(0x12345678) -> 0x78563412[/dim])
  • 定数: [bold]pi[/bold] (円周率), [bold]e[/bold] (自然対数の底)
"""


class HelpScreen(ModalScreen[None]):
    """Modal help and reference dialog."""

    BINDINGS = [
        Binding("escape", "dismiss_help", "Close", priority=True),
        Binding("enter", "dismiss_help", "Close", priority=True),
        Binding("q", "dismiss_help", "Close", priority=True),
        Binding("f1", "dismiss_help", "Close", priority=True),
        Binding("question_mark", "dismiss_help", "Close", priority=True),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }

    #help-dialog {
        width: 80;
        height: 80%;
        border: thick $primary;
        background: $panel;
        padding: 1 2;
    }

    #help-scroll {
        height: 1fr;
    }

    #close-btn {
        dock: bottom;
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            with ScrollableContainer(id="help-scroll"):
                yield Static(HELP_MARKDOWN)
            yield Button("閉じる (Esc / Enter)", id="close-btn", variant="primary")

    def action_dismiss_help(self) -> None:
        self.dismiss(None)

    def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "enter", "q", "f1", "question_mark"):
            self.dismiss(None)
            event.prevent_default()
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss(None)
