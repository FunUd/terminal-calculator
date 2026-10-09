"""Configuration module with persistence support."""

from dataclasses import dataclass, asdict
from calc.evaluator import AngleMode
import json
import os
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    angle_mode: AngleMode = AngleMode.DEG
    bit_width: int = 32
    max_history: int = 100
    theme: str = "default"

    @staticmethod
    def get_config_path() -> Path:
        """Get the path to the config file in user's home directory."""
        config_dir = Path.home() / ".config" / "terminal-calculator"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file, or return default if not exists."""
        config_path = cls.get_config_path()
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert angle_mode string back to enum
            if "angle_mode" in data:
                data["angle_mode"] = AngleMode[data["angle_mode"]]

            return cls(**data)
        except (json.JSONDecodeError, KeyError, ValueError):
            # If config is corrupted, return default
            return cls()

    def save(self) -> None:
        """Save configuration to file."""
        config_path = self.get_config_path()
        data = asdict(self)
        # Convert AngleMode enum to string for JSON serialization
        data["angle_mode"] = self.angle_mode.name

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
