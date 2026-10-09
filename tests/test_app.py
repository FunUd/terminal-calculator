import pytest
from calc.app import CalculatorApp, HistoryAwareInput
from calc.evaluator import AngleMode
from textual.widgets import Static, OptionList


@pytest.mark.asyncio
async def test_app_input_and_results():
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)
        inp.value = "0xFF + 10"
        await pilot.pause()

        assert str(app.query_one("#val-dec", Static).content) == "265"
        assert str(app.query_one("#val-hex", Static).content) == "0x109"
        assert str(app.query_one("#val-bin", Static).content) == "0b1_0000_1001"
        assert str(app.query_one("#val-signed", Static).content) == "265"


@pytest.mark.asyncio
async def test_app_history_submission_and_navigation():
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Enter first expression
        inp.value = "10 + 20"
        await pilot.press("enter")
        await pilot.pause()

        assert len(app.history_mgr.items) == 1

        # Enter second expression
        inp.value = "30 + 40"
        await pilot.press("enter")
        await pilot.pause()

        assert len(app.history_mgr.items) == 2

        # Test Up arrow history navigation
        inp.value = "draft"
        await pilot.press("up")
        await pilot.pause()
        assert inp.value == "30 + 40"

        await pilot.press("up")
        await pilot.pause()
        assert inp.value == "10 + 20"

        # Down arrow returns to later history and draft
        await pilot.press("down")
        await pilot.pause()
        assert inp.value == "30 + 40"

        await pilot.press("down")
        await pilot.pause()
        assert inp.value == "draft"


@pytest.mark.asyncio
async def test_app_toggle_angle_mode():
    app = CalculatorApp()
    async with app.run_test() as pilot:
        assert app.angle_mode == AngleMode.DEG

        inp = app.query_one("#expr-input", HistoryAwareInput)
        inp.value = "sin(90)"
        await pilot.pause()
        assert str(app.query_one("#val-dec", Static).content) == "1"

        # Toggle to RAD with F2
        await pilot.press("f2")
        await pilot.pause()
        assert app.angle_mode == AngleMode.RAD

        # Toggle back to DEG
        await pilot.press("f2")
        await pilot.pause()
        assert app.angle_mode == AngleMode.DEG


@pytest.mark.asyncio
async def test_app_clear_and_error_handling():
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Incomplete / invalid input
        inp.value = "1 / 0"
        await pilot.pause()
        err_box = app.query_one("#error-box", Static)
        assert "Division by zero" in str(err_box.content)

        # Clear input with escape
        await pilot.press("escape")
        await pilot.pause()
        assert inp.value == ""
        assert str(app.query_one("#val-dec", Static).content) == "-"
        assert str(app.query_one("#error-box", Static).content) == ""


@pytest.mark.asyncio
async def test_app_ans_and_history_referencing():
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # 1st calculation: 10 + 20 = 30
        inp.value = "10 + 20"
        await pilot.press("enter")
        await pilot.pause()

        # 2nd calculation using 'ans': ans * 2 = 60
        inp.value = "ans * 2"
        await pilot.pause()
        assert str(app.query_one("#val-dec", Static).content) == "60"

        # Submit 2nd calculation
        await pilot.press("enter")
        await pilot.pause()

        # 3rd calculation using history variable 'h1' and '$2'
        inp.value = "h1 + $2"
        await pilot.pause()
        assert str(app.query_one("#val-dec", Static).content) == "90"  # 30 + 60

        # Bitfield visualizer test (64-bit)
        bit_grid = str(app.query_one("#bit-grid-text", Static).content)
        assert "[63..48]" in bit_grid


@pytest.mark.asyncio
async def test_app_help_screen():
    from calc.help_screen import HelpScreen

    app = CalculatorApp()
    async with app.run_test() as pilot:
        # Press F1 to open help screen
        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, HelpScreen)

        # Press Escape to dismiss
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, HelpScreen)


@pytest.mark.asyncio
async def test_app_copy_screen():
    from calc.copy_screen import CopyScreen

    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)
        inp.value = "0xFF + 10"  # 265
        await pilot.pause()

        # Press F4 to open CopyScreen
        await pilot.press("f4")
        await pilot.pause()
        assert isinstance(app.screen, CopyScreen)

        # Press '2' to copy HEX (0x109) and dismiss
        await pilot.press("2")
        await pilot.pause()
        assert not isinstance(app.screen, CopyScreen)


@pytest.mark.asyncio
async def test_alt_insert_history_by_number():
    """Alt+1 inserts history #1 result; Alt+2 inserts history #2 result."""
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Submit first expression: 4 + 4 = 8 (id=1)
        inp.value = "4 + 4"
        await pilot.press("enter")
        await pilot.pause()

        # Submit second expression: 10 + 5 = 15 (id=2)
        inp.value = "10 + 5"
        await pilot.press("enter")
        await pilot.pause()

        # Set input to "2 + 2 + " with cursor at end
        inp.value = "2 + 2 + "
        inp.cursor_position = len(inp.value)
        await pilot.pause()

        # Alt+1 inserts "8" at cursor
        await pilot.press("alt+1")
        await pilot.pause()
        assert inp.value == "2 + 2 + 8"
        assert inp.cursor_position == 9

        # Alt+2 inserts "15" at end of current value
        await pilot.press("alt+2")
        await pilot.pause()
        assert inp.value == "2 + 2 + 815"
        assert inp.cursor_position == 11


@pytest.mark.asyncio
async def test_alt_insert_ans():
    """Alt+A inserts the most recent result (ans) at the cursor position."""
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Submit expression: 3 * 7 = 21
        inp.value = "3 * 7"
        await pilot.press("enter")
        await pilot.pause()

        # Set input to "100 - " with cursor at end
        inp.value = "100 - "
        inp.cursor_position = len(inp.value)
        await pilot.pause()

        # Alt+A inserts "21"
        await pilot.press("alt+a")
        await pilot.pause()
        assert inp.value == "100 - 21"
        assert inp.cursor_position == 8


@pytest.mark.asyncio
async def test_alt_insert_nonexistent_history():
    """Alt+9 and Alt+A with empty history do nothing."""
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Empty history: Alt+9 does nothing
        inp.value = "5 + "
        inp.cursor_position = len(inp.value)
        await pilot.pause()

        await pilot.press("alt+9")
        await pilot.pause()
        assert inp.value == "5 + "

        # Empty history: Alt+A does nothing
        await pilot.press("alt+a")
        await pilot.pause()
        assert inp.value == "5 + "


@pytest.mark.asyncio
async def test_alt_insert_middle_of_text():
    """Inserting at a cursor position that is not at the end works correctly."""
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Submit expression: 5 + 5 = 10 (id=1)
        inp.value = "5 + 5"
        await pilot.press("enter")
        await pilot.pause()

        # Set input to "100 + 200" with cursor in the middle (after "100 ")
        inp.value = "100 + 200"
        inp.cursor_position = 4  # after "100 "
        await pilot.pause()

        # Alt+A inserts "10" at position 4
        await pilot.press("alt+a")
        await pilot.pause()
        assert inp.value == "100 10+ 200"
        assert inp.cursor_position == 6


@pytest.mark.asyncio
async def test_alt_insert_middle_of_text_numbered():
    """Alt+N inserts at a non-end cursor position, same as Alt+A."""
    app = CalculatorApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        # Submit expression: 7 + 3 = 10 (id=1, position 0)
        inp.value = "7 + 3"
        await pilot.press("enter")
        await pilot.pause()

        # Set input to "500 - 200" with cursor after "500 " (position 4)
        inp.value = "500 - 200"
        inp.cursor_position = 4
        await pilot.pause()

        # Alt+1 inserts "10" at position 4
        await pilot.press("alt+1")
        await pilot.pause()
        assert inp.value == "500 10- 200"
        assert inp.cursor_position == 6


@pytest.mark.asyncio
async def test_alt_insert_overflow_position_based():
    """After overflow Alt+N uses 1-based list index, not item ID.

    Values are multiples of 10 so result_repr ('30', '70') never equals
    item.id (3, 7), making index-vs-ID bugs detectable.
    """
    from calc.config import Config

    # max_size=5; submit 7 × 10-multiples
    # Evicted: "10" (id=1), "20" (id=2)
    # Survivors: items[0]="30"(id=3) … items[4]="70"(id=7)
    app = CalculatorApp(config=Config(max_history=5))
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        for i in range(1, 8):
            inp.value = f"{i * 10}"
            await pilot.press("enter")
            await pilot.pause()

        assert len(app.history_mgr.items) == 5

        inp.value = "0 + "
        inp.cursor_position = len(inp.value)
        await pilot.pause()

        # Alt+1 → items[0].result_repr == "30" (NOT "10" which was evicted)
        await pilot.press("alt+1")
        await pilot.pause()
        assert inp.value == "0 + 30", (
            f"Expected '0 + 30' but got '{inp.value}'; "
            "Alt+1 must resolve by list index, not item ID"
        )

        # Alt+5 → items[4].result_repr == "70"
        inp.value = "0 + "
        inp.cursor_position = len(inp.value)
        await pilot.pause()
        await pilot.press("alt+5")
        await pilot.pause()
        assert inp.value == "0 + 70", (
            f"Expected '0 + 70' but got '{inp.value}'"
        )

        # Alt+6 → out-of-range (only 5 items), nothing inserted
        inp.value = "0 + "
        inp.cursor_position = len(inp.value)
        await pilot.pause()
        await pilot.press("alt+6")
        await pilot.pause()
        assert inp.value == "0 + "


@pytest.mark.asyncio
async def test_history_panel_labels_match_alt_n_index():
    """History panel labels must show 1-based list position, not item.id.

    After overflow, the oldest survivor must show '#1', newest '#N',
    so the label a user reads matches the Alt+N key they should press.
    """
    from calc.config import Config
    from textual.widgets.option_list import Option

    app = CalculatorApp(config=Config(max_history=5))
    async with app.run_test() as pilot:
        inp = app.query_one("#expr-input", HistoryAwareInput)

        for i in range(1, 8):
            inp.value = f"{i * 10}"
            await pilot.press("enter")
            await pilot.pause()

        opt_list = app.query_one("#history-list", OptionList)
        # OptionList displays newest first.
        # Newest = items[4] (result "70") → label "#5"
        # Oldest = items[0] (result "30") → label "#1"
        labels = [str(opt.prompt) for opt in opt_list._options]

        assert labels[0].startswith("#5 "), (
            f"Newest entry should be '#5 …' but got: {labels[0]!r}"
        )
        assert labels[-1].startswith("#1 "), (
            f"Oldest entry should be '#1 …' but got: {labels[-1]!r}"
        )
        # Confirm none of the labels use the stale item IDs (#3..#7)
        for label in labels:
            num = int(label.split()[0][1:])   # strip '#', convert to int
            assert 1 <= num <= 5, (
                f"Panel label {label!r} is outside [#1..#5]; "
                "labels must reflect list position, not item ID"
            )


@pytest.mark.asyncio
async def test_theme_toggle():
    """Test F3 theme cycling functionality."""
    app = CalculatorApp()
    async with app.run_test() as pilot:
        # THEMES should be populated after mount
        assert len(app.THEMES) > 0

        initial_theme = app.theme
        initial_index = app._theme_index

        # Press F3 to cycle theme
        await pilot.press("f3")
        await pilot.pause()

        # Theme should have changed if there are multiple themes
        if len(app.THEMES) > 1:
            assert app.theme != initial_theme
            assert app._theme_index == (initial_index + 1) % len(app.THEMES)
