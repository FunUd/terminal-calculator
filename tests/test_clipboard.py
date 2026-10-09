from calc.clipboard import copy_to_clipboard


def test_copy_to_clipboard():
    # Should not raise exception even without terminal / GUI
    success = copy_to_clipboard("test_123")
    assert isinstance(success, bool)
