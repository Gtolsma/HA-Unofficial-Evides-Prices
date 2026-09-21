"""DataUpdateCoordinator for Evides Tarieven.

Scrapes the public Evides tariff page (https://www.evides.nl/service/tarieven)
for the yearly drinking-water tariffs (vastrecht, variabel tarief per m3 and
belasting op leidingwater per m3).

The page has no stable CSS classes/ids to rely on, so parsing is done by
matching Dutch label text in the table rows rather than by selector. This is
inherently fragile against a redesign of the Evides website; if Evides
changes the wording of the row labels this integration will stop finding
values and will raise an UpdateFailed, which shows up as the sensors going
unavailable rather than silently returning wrong numbers.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_BRON_URL,
    ATTR_JAAR,
    ATTR_JAAR_BRON,
    ATTR_LAATST_GECONTROLEERD,
    DOMAIN,
    KEY_BELASTING_LEIDINGWATER,
    KEY_VARIABEL_TARIEF,
    KEY_VASTRECHT,
    TARIEVEN_URL,
)

_LOGGER = logging.getLogger(__name__)

# Row-label matchers -> data key. Matched case-insensitively against the
# text of the *first* cell of each table row. Order matters: more specific
# patterns first.
_LABEL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"vastrecht", re.IGNORECASE), KEY_VASTRECHT),
    (re.compile(r"variabel\s+tarief", re.IGNORECASE), KEY_VARIABEL_TARIEF),
    (
        re.compile(r"belasting\s+op\s+leidingwater|\bbol\b", re.IGNORECASE),
        KEY_BELASTING_LEIDINGWATER,
    ),
]

_PRICE_RE = re.compile(r"€\s*([\d.,]+)")
_YEAR_PATTERNS = [
    re.compile(r"Tarievenregeling\s+(20\d{2})", re.IGNORECASE),
    re.compile(r"Drinkwatertarieven\s+(20\d{2})", re.IGNORECASE),
    re.compile(r"tarieven\s+(20\d{2})", re.IGNORECASE),
]


def _parse_euro(text: str) -> float | None:
    """Parse a Dutch-formatted euro amount like '€ 1.674,24' or '€ 0,476*'."""
    match = _PRICE_RE.search(text)
    if not match:
        return None
    raw = match.group(1).rstrip(".,")
    # NL formatting: '.' is a thousands separator, ',' is the decimal comma.
    raw = raw.replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_tarieven(html: str) -> dict[str, Any]:
    """Parse the Evides tarieven page HTML into a data dict.

    Raises ValueError if none of the expected tariff rows could be found,
    which signals the caller that the page layout likely changed.
    """
    soup = BeautifulSoup(html, "html.parser")

    results: dict[str, float] = {}

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            label_text = cells[0].get_text(strip=True)
            if not label_text:
                continue
            for pattern, key in _LABEL_PATTERNS:
                if key in results:
                    continue
                if pattern.search(label_text):
                    # Price is usually the last cell (the "incl. btw" column).
                    price = None
                    for cell in reversed(cells[1:]):
                        price = _parse_euro(cell.get_text(" ", strip=True))
                        if price is not None:
                            break
                    if price is not None:
                        results[key] = price
                    break

    if not results:
        raise ValueError(
            "Kon geen enkel bekend tarief vinden op de Evides-tarievenpagina; "
            "de paginastructuur is mogelijk gewijzigd."
        )

    page_text = soup.get_text(" ", strip=True)
    jaar: int | None = None
    for pattern in _YEAR_PATTERNS:
        match = pattern.search(page_text)
        if match:
            jaar = int(match.group(1))
            break

    return {
        "values": results,
        ATTR_JAAR: jaar if jaar is not None else datetime.now().year,
        ATTR_JAAR_BRON: "pagina" if jaar is not None else "geschat (huidig jaar)",
    }


class EvidesTariefCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that periodically scrapes the Evides tarieven page."""

    def __init__(self, hass: HomeAssistant, update_interval) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(TARIEVEN_URL, timeout=30) as response:
                response.raise_for_status()
                html = await response.text()
        except Exception as err:  # noqa: BLE001 - surfaced via UpdateFailed
            raise UpdateFailed(f"Kon Evides-tarievenpagina niet ophalen: {err}") from err

        try:
            parsed = await self.hass.async_add_executor_job(parse_tarieven, html)
        except ValueError as err:
            raise UpdateFailed(str(err)) from err

        parsed[ATTR_BRON_URL] = TARIEVEN_URL
        parsed[ATTR_LAATST_GECONTROLEERD] = datetime.now(timezone.utc).isoformat()
        return parsed
