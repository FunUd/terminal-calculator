"""Calculation history management."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class HistoryItem:
    id: int
    expr: str
    result_repr: str
    raw_value: Optional[Union[int, float]] = None


class HistoryManager:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.items: list[HistoryItem] = []
        self._current_index: Optional[int] = None
        self._draft: str = ""
        self._next_id: int = 1

    def add(self, expr: str, result_repr: str, raw_value: Optional[Union[int, float]] = None) -> None:
        expr = expr.strip()
        if not expr:
            return
        # Ignore duplicate if same as the last item
        if self.items and self.items[-1].expr == expr:
            return

        item = HistoryItem(
            id=self._next_id,
            expr=expr,
            result_repr=result_repr,
            raw_value=raw_value,
        )
        self._next_id += 1

        self.items.append(item)
        if len(self.items) > self.max_size:
            self.items.pop(0)

        self.reset_navigation()

    def reset_navigation(self) -> None:
        self._current_index = None
        self._draft = ""

    def get_variables(self) -> dict[str, Union[int, float]]:
        """Return a mapping of history variables such as 'ans', 'h1', '$1', etc."""
        mapping: dict[str, Union[int, float]] = {}
        for item in self.items:
            if item.raw_value is not None:
                mapping[f"h{item.id}"] = item.raw_value
                mapping[f"${item.id}"] = item.raw_value
        if self.items and self.items[-1].raw_value is not None:
            mapping["ans"] = self.items[-1].raw_value
        return mapping

    def get_previous(self, current_draft: str) -> Optional[str]:
        if not self.items:
            return None

        if self._current_index is None:
            self._draft = current_draft
            self._current_index = len(self.items) - 1
        elif self._current_index > 0:
            self._current_index -= 1

        return self.items[self._current_index].expr

    def get_next(self) -> Optional[str]:
        if not self.items or self._current_index is None:
            return None

        if self._current_index < len(self.items) - 1:
            self._current_index += 1
            return self.items[self._current_index].expr
        else:
            self._current_index = None
            return self._draft
