"""Tests for configuration persistence."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from calc.config import Config
from calc.evaluator import AngleMode


def test_config_default_values():
    """Test that config has correct default values."""
    config = Config()
    assert config.angle_mode == AngleMode.DEG
    assert config.bit_width == 32
    assert config.max_history == 100
    assert config.theme == "default"


def test_config_save_and_load():
    """Test that config can be saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        with patch.object(Config, 'get_config_path', return_value=config_path):
            # Create and save a config
            config1 = Config(angle_mode=AngleMode.RAD, theme="monokai", max_history=50)
            config1.save()

            # Load the config
            config2 = Config.load()

            assert config2.angle_mode == AngleMode.RAD
            assert config2.theme == "monokai"
            assert config2.max_history == 50


def test_config_load_default_when_missing():
    """Test that load returns default config when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "nonexistent.json"

        with patch.object(Config, 'get_config_path', return_value=config_path):
            config = Config.load()
            assert config.angle_mode == AngleMode.DEG
            assert config.theme == "default"


def test_config_load_handles_corrupted_file():
    """Test that load returns default config when file is corrupted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"

        with patch.object(Config, 'get_config_path', return_value=config_path):
            # Write invalid JSON
            config_path.write_text("{ invalid json }")

            config = Config.load()
            assert config.angle_mode == AngleMode.DEG
            assert config.theme == "default"
