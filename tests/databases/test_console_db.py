"""Tests for the Console Database module."""

import pytest
from loguru import logger
import sys

from webkeeper.core import Metadata
from webkeeper.modules.console_db.console_db import ConsoleDb


@pytest.fixture
def console_db():
    """Create a ConsoleDb instance."""
    db = ConsoleDb()
    db.name = "console_db"
    db.config = {}
    return db


@pytest.fixture
def item():
    """Create a test Metadata item."""
    return Metadata().set_url("https://example.com/test")


@pytest.fixture
def capture_logs(capsys):
    """Capture loguru output."""
    logger.remove()
    logger.add(sys.stderr, format="{level} {message}")
    yield
    logger.remove()


class TestConsoleDbLogging:
    """Test console database logging methods."""

    def test_started_logs_info(self, console_db, item, capture_logs, capsys):
        """started() logs an info message."""
        console_db.started(item)

        captured = capsys.readouterr()
        assert "STARTED" in captured.err
        assert "example.com" in captured.err

    def test_failed_logs_error_with_reason(self, console_db, item, capture_logs, capsys):
        """failed() logs error with reason."""
        console_db.failed(item, "Connection timeout")

        captured = capsys.readouterr()
        assert "FAILED" in captured.err
        assert "Connection timeout" in captured.err

    def test_aborted_logs_warning(self, console_db, item, capture_logs, capsys):
        """aborted() logs a warning message."""
        console_db.aborted(item)

        captured = capsys.readouterr()
        assert "ABORTED" in captured.err

    def test_done_logs_success(self, console_db, item, capture_logs, capsys):
        """done() logs a success message."""
        console_db.done(item)

        captured = capsys.readouterr()
        assert "DONE" in captured.err

    def test_done_with_cached_flag(self, console_db, item, capture_logs, capsys):
        """done() accepts cached parameter."""
        console_db.done(item, cached=True)

        captured = capsys.readouterr()
        assert "DONE" in captured.err


class TestConsoleDbInterface:
    """Test console database interface compliance."""

    def test_implements_database_methods(self, console_db):
        """ConsoleDb implements all required Database methods."""
        assert hasattr(console_db, 'started')
        assert hasattr(console_db, 'failed')
        assert hasattr(console_db, 'aborted')
        assert hasattr(console_db, 'done')

    def test_fetch_returns_false(self, console_db, item):
        """fetch() returns False (no caching)."""
        result = console_db.fetch(item)
        assert result is False
