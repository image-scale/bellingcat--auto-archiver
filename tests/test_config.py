"""Tests for the configuration system."""

import pytest
import os

from webkeeper.core.config import (
    read_yaml,
    store_yaml,
    to_dot_notation,
    from_dot_notation,
    merge_dicts,
    is_valid_config,
    EMPTY_CONFIG,
    DEFAULT_CONFIG_FILE,
)


class TestReadYaml:
    """Test YAML reading functionality."""

    def test_read_yaml_existing_file(self, tmp_path):
        """read_yaml loads existing YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
steps:
  feeders:
    - cli_feeder
  extractors:
    - generic
logging:
  level: DEBUG
""")

        config = read_yaml(str(config_file))

        assert config["steps"]["feeders"] == ["cli_feeder"]
        assert config["steps"]["extractors"] == ["generic"]
        assert config["logging"]["level"] == "DEBUG"

    def test_read_yaml_missing_file_returns_empty_config(self, tmp_path):
        """read_yaml returns empty config for missing file."""
        config = read_yaml(str(tmp_path / "nonexistent.yaml"))

        assert "steps" in config
        assert config["steps"]["feeders"] == []
        assert config["steps"]["extractors"] == []

    def test_read_yaml_empty_file_returns_empty_config(self, tmp_path):
        """read_yaml returns empty config for empty file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = read_yaml(str(config_file))

        assert "steps" in config


class TestStoreYaml:
    """Test YAML writing functionality."""

    def test_store_yaml_creates_file(self, tmp_path):
        """store_yaml creates YAML file."""
        config_file = tmp_path / "output.yaml"
        config = {
            "steps": {"feeders": ["cli_feeder"]},
            "logging": {"level": "INFO"}
        }

        store_yaml(config, str(config_file))

        assert config_file.exists()
        content = config_file.read_text()
        assert "feeders" in content

    def test_store_yaml_creates_directory(self, tmp_path):
        """store_yaml creates parent directories."""
        config_file = tmp_path / "subdir" / "config.yaml"
        config = {"steps": {"feeders": []}}

        store_yaml(config, str(config_file))

        assert config_file.exists()

    def test_store_yaml_excludes_urls(self, tmp_path):
        """store_yaml excludes urls from output."""
        config_file = tmp_path / "output.yaml"
        config = {
            "steps": {"feeders": []},
            "urls": ["https://example.com"]
        }

        store_yaml(config, str(config_file))

        content = config_file.read_text()
        assert "urls" not in content


class TestToDotNotation:
    """Test flattening nested dicts."""

    def test_simple_flat_dict(self):
        """Flat dict returns prefixed keys."""
        result = to_dot_notation({"key": "value"})
        assert result == {"key": "value"}

    def test_nested_dict(self):
        """Nested dict is flattened with dots."""
        result = to_dot_notation({
            "logging": {
                "level": "INFO",
                "file": "/tmp/log.txt"
            }
        })
        assert result == {
            "logging.level": "INFO",
            "logging.file": "/tmp/log.txt"
        }

    def test_deeply_nested_dict(self):
        """Deeply nested dict is fully flattened."""
        result = to_dot_notation({
            "a": {"b": {"c": "value"}}
        })
        assert result == {"a.b.c": "value"}

    def test_mixed_values(self):
        """Lists and other types are preserved."""
        result = to_dot_notation({
            "steps": {"feeders": ["a", "b"]},
            "logging": {"level": "INFO"}
        })
        assert result["steps.feeders"] == ["a", "b"]
        assert result["logging.level"] == "INFO"


class TestFromDotNotation:
    """Test restoring nested dicts."""

    def test_simple_keys(self):
        """Simple keys stay as-is."""
        result = from_dot_notation({"key": "value"})
        assert result == {"key": "value"}

    def test_dotted_keys(self):
        """Dotted keys become nested."""
        result = from_dot_notation({
            "logging.level": "INFO",
            "logging.file": "/tmp/log.txt"
        })
        assert result == {
            "logging": {
                "level": "INFO",
                "file": "/tmp/log.txt"
            }
        }

    def test_deeply_dotted_keys(self):
        """Multiple dots create deep nesting."""
        result = from_dot_notation({"a.b.c": "value"})
        assert result == {"a": {"b": {"c": "value"}}}

    def test_roundtrip(self):
        """to_dot_notation and from_dot_notation are inverses."""
        original = {
            "logging": {"level": "INFO"},
            "module": {"setting": "value"}
        }
        dotted = to_dot_notation(original)
        restored = from_dot_notation(dotted)
        assert restored == original


class TestMergeDicts:
    """Test config merging."""

    def test_merge_adds_new_keys(self):
        """merge_dicts adds keys from CLI."""
        cli = {"new_key": "value"}
        yaml_config = {"existing": "data"}

        result = merge_dicts(cli, yaml_config)

        assert result["existing"] == "data"
        assert result["new_key"] == "value"

    def test_merge_overwrites_values(self):
        """merge_dicts overwrites existing values."""
        cli = {"logging.level": "DEBUG"}
        yaml_config = {"logging": {"level": "INFO"}}

        result = merge_dicts(cli, yaml_config)

        assert result["logging"]["level"] == "DEBUG"

    def test_merge_extends_lists(self):
        """merge_dicts extends list values."""
        cli = {"tags": ["c", "d"]}
        yaml_config = {"tags": ["a", "b"]}

        result = merge_dicts(cli, yaml_config)

        assert "a" in result["tags"]
        assert "b" in result["tags"]
        assert "c" in result["tags"]
        assert "d" in result["tags"]

    def test_merge_steps_overwrites(self):
        """merge_dicts overwrites steps completely."""
        cli = {"steps.feeders": ["new_feeder"]}
        yaml_config = {"steps": {"feeders": ["old_feeder"], "extractors": []}}

        result = merge_dicts(cli, yaml_config)

        assert result["steps"]["feeders"] == ["new_feeder"]

    def test_merge_preserves_original(self):
        """merge_dicts doesn't modify original dict."""
        cli = {"key": "new"}
        yaml_config = {"key": "original"}

        merge_dicts(cli, yaml_config)

        assert yaml_config["key"] == "original"


class TestIsValidConfig:
    """Test config validation."""

    def test_empty_config_is_invalid(self):
        """Empty config is not valid."""
        assert is_valid_config(None) is False
        assert is_valid_config({}) is False

    def test_default_config_is_invalid(self):
        """Default empty config is not valid."""
        assert is_valid_config(EMPTY_CONFIG) is False

    def test_modified_config_is_valid(self):
        """Config with changes is valid."""
        config = {"steps": {"feeders": ["cli_feeder"]}, "custom": "value"}
        assert is_valid_config(config) is True


class TestConstants:
    """Test module constants."""

    def test_default_config_file(self):
        """DEFAULT_CONFIG_FILE has expected value."""
        assert DEFAULT_CONFIG_FILE == "config.yaml"

    def test_empty_config_has_steps(self):
        """EMPTY_CONFIG has steps section."""
        assert "steps" in EMPTY_CONFIG
        assert "feeders" in EMPTY_CONFIG["steps"]
        assert "extractors" in EMPTY_CONFIG["steps"]
        assert "enrichers" in EMPTY_CONFIG["steps"]
        assert "databases" in EMPTY_CONFIG["steps"]
        assert "storages" in EMPTY_CONFIG["steps"]
        assert "formatters" in EMPTY_CONFIG["steps"]

    def test_empty_config_has_authentication(self):
        """EMPTY_CONFIG has authentication section."""
        assert "authentication" in EMPTY_CONFIG

    def test_empty_config_has_logging(self):
        """EMPTY_CONFIG has logging section."""
        assert "logging" in EMPTY_CONFIG
        assert EMPTY_CONFIG["logging"]["level"] == "INFO"
