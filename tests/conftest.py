"""Fixtures for Evides Tarieven tests."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    yield


@pytest.fixture
def tarieven_html() -> str:
    """Trimmed copy of the real Evides tarieven page."""
    return (FIXTURES / "tarieven_2026.html").read_text(encoding="utf-8")
