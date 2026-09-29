"""Tests for the HTML parser."""
from __future__ import annotations

import pytest

from custom_components.evides_tarieven.coordinator import _parse_euro, parse_tarieven


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("€ 101,05", 101.05),
        ("€ 0,476*", 0.476),
        ("€ 1.674,24", 1674.24),
        ("€1,320", 1.32),
        ("Gratis", None),
        ("", None),
    ],
)
def test_parse_euro(text: str, expected: float | None) -> None:
    assert _parse_euro(text) == expected


def test_parse_real_page(tarieven_html: str) -> None:
    result = parse_tarieven(tarieven_html)
    assert result["values"] == {
        "vastrecht": 101.05,
        "variabel_tarief": 1.32,
        "belasting_leidingwater": 0.476,
    }
    assert result["jaar"] == 2026
    assert result["jaar_bron"] == "pagina"


def test_parse_ignores_unrelated_tables(tarieven_html: str) -> None:
    # The connection-costs table must never leak into the tariffs.
    result = parse_tarieven(tarieven_html)
    assert 1674.24 not in result["values"].values()


def test_parse_partial() -> None:
    html = "<table><tr><td>Vastrecht per jaar</td><td>€ 99,00</td></tr></table>"
    result = parse_tarieven(html)
    assert result["values"] == {"vastrecht": 99.0}
    assert result["jaar_bron"] == "geschat (huidig jaar)"


def test_parse_nothing_found() -> None:
    with pytest.raises(ValueError):
        parse_tarieven("<html><body><p>Onderhoud</p></body></html>")
