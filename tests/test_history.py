from calc.history import HistoryManager


def test_history_empty():
    hm = HistoryManager()
    assert hm.get_previous("") is None
    assert hm.get_next() is None
    assert len(hm.items) == 0


def test_history_add_and_navigation():
    hm = HistoryManager()
    hm.add("1 + 1", "2")
    hm.add("2 + 2", "4")
    hm.add("3 + 3", "6")

    # Navigate up (previous)
    # Draft is "draft_expr"
    assert hm.get_previous("draft_expr") == "3 + 3"
    assert hm.get_previous("draft_expr") == "2 + 2"
    assert hm.get_previous("draft_expr") == "1 + 1"
    # Reaching top doesn't crash or go further
    assert hm.get_previous("draft_expr") == "1 + 1"

    # Navigate down (next)
    assert hm.get_next() == "2 + 2"
    assert hm.get_next() == "3 + 3"
    assert hm.get_next() == "draft_expr"  # restore original draft
    assert hm.get_next() is None


def test_history_duplicate_ignore_consecutive():
    hm = HistoryManager()
    hm.add("1 + 1", "2")
    hm.add("1 + 1", "2")
    assert len(hm.items) == 1


def test_history_max_size():
    hm = HistoryManager(max_size=3)
    hm.add("1", "1")
    hm.add("2", "2")
    hm.add("3", "3")
    hm.add("4", "4")
    assert len(hm.items) == 3
    assert hm.items[0].expr == "2"
    assert hm.items[-1].expr == "4"


def test_history_variables():
    hm = HistoryManager()
    assert hm.get_variables() == {}

    hm.add("10 + 20", "30", raw_value=30)
    assert hm.get_variables() == {"ans": 30, "h1": 30, "$1": 30}

    hm.add("sqrt(16)", "4", raw_value=4)
    vars_map = hm.get_variables()
    assert vars_map["ans"] == 4
    assert vars_map["h1"] == 30
    assert vars_map["$1"] == 30
    assert vars_map["h2"] == 4
    assert vars_map["$2"] == 4

