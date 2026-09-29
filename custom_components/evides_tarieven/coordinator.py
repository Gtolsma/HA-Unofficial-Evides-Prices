"""DataUpdateCoordinator for Evides Tarieven.

Scrapes the public Evides tariff page (https://www.evides.nl/service/tarieven)
for the yearly drinking-water tariffs (vastrecht, variabel tarief per m3 and
belasting op leidingwater per m3).

The page has no stable CSS classes/ids to rely on, so parsing is done by
matching Dutch label text in the table rows rather than by selector. This is
inherently fragile against a redesign of the Evides website; if Evides
changes the wording of the row labels this integration will stop finding
values, raise a repair issue and mark the affected sensors unavailable rather
than silently returning wrong numbers.

Plain network errors are treated differently: the tariffs only change once a
year, so the last successfully scraped values (also persisted to disk, so they
survive a restart) are kept instead of making every sensor unavailable while
evides.nl is briefly unreachable.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_BRON_URL,
    ATTR_JAAR,
    ATTR_JAAR_BRON,
    ATTR_LAATST_GECONTROLEERD,
    DOMAIN,
    EVENT_TARIEF_GEWIJZIGD,
    ISSUE_PAGINA_GEWIJZIGD,
    KEY_BELASTING_LEIDINGWATER,
    KEY_VARIABEL_TARIEF,
    KEY_VASTRECHT,
    REQUEST_TIMEOUT_SECONDS,
    SCRAPED_KEYS,
    TARIEVEN_URL,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1

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

# Human-readable labels used in the repair issue for missing rows.
_KEY_LABELS = {
    KEY_VASTRECHT: "Vastrecht",
    KEY_VARIABEL_TARIEF: "Variabel tarief",
    KEY_BELASTING_LEIDINGWATER: "Belasting op Leidingwater (BoL)",
}

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
        ATTR_JAAR: jaar if jaar is not None else dt_util.now().year,
        ATTR_JAAR_BRON: "pagina" if jaar is not None else "geschat (huidig jaar)",
    }


def cache_store(hass: HomeAssistant, entry: ConfigEntry) -> Store[dict[str, Any]]:
    """Return the store holding the last successfully scraped tariffs."""
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")


class EvidesTariefCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that periodically scrapes the Evides tarieven page."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, update_interval
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._store = cache_store(hass, entry)
        self._cache: dict[str, Any] | None = None

    async def async_load_cache(self) -> None:
        """Load the last successfully scraped tariffs from disk."""
        self._cache = await self._store.async_load()

    async def _async_update_data(self) -> dict[str, Any]:
        previous = self.data or self._cache

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                TARIEVEN_URL,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
            ) as response:
                response.raise_for_status()
                html = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            if previous is not None:
                _LOGGER.warning(
                    "Kon Evides-tarievenpagina niet ophalen (%s); de laatst "
                    "bekende tarieven van %s blijven in gebruik",
                    err,
                    previous.get(ATTR_LAATST_GECONTROLEERD),
                )
                return previous
            raise UpdateFailed(f"Kon Evides-tarievenpagina niet ophalen: {err}") from err

        try:
            parsed = await self.hass.async_add_executor_job(parse_tarieven, html)
        except ValueError as err:
            self._async_create_page_issue(list(SCRAPED_KEYS))
            raise UpdateFailed(str(err)) from err

        missing = [key for key in SCRAPED_KEYS if key not in parsed["values"]]
        if missing:
            _LOGGER.warning(
                "Niet alle tarieven gevonden op de Evides-pagina, ontbrekend: %s",
                ", ".join(missing),
            )
            self._async_create_page_issue(missing)
        else:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PAGINA_GEWIJZIGD)

        parsed[ATTR_BRON_URL] = TARIEVEN_URL
        parsed[ATTR_LAATST_GECONTROLEERD] = dt_util.utcnow().isoformat()

        if previous is not None:
            self._async_fire_change_event(previous, parsed)

        self._cache = parsed
        await self._store.async_save(parsed)
        return parsed

    def _async_create_page_issue(self, missing: list[str]) -> None:
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            ISSUE_PAGINA_GEWIJZIGD,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_PAGINA_GEWIJZIGD,
            translation_placeholders={
                "ontbrekend": ", ".join(_KEY_LABELS[key] for key in missing),
                "url": TARIEVEN_URL,
            },
            learn_more_url="https://github.com/Gtolsma/HA-Unofficial-Evides-Prices/issues",
        )

    def _async_fire_change_event(
        self, previous: dict[str, Any], current: dict[str, Any]
    ) -> None:
        """Fire an event when one or more tariffs changed since the last check."""
        oud = previous.get("values", {})
        nieuw = current["values"]
        gewijzigd = [
            key for key in nieuw if key in oud and oud[key] != nieuw[key]
        ]
        if not gewijzigd:
            return
        _LOGGER.info("Evides-tarieven gewijzigd: %s", ", ".join(gewijzigd))
        self.hass.bus.async_fire(
            EVENT_TARIEF_GEWIJZIGD,
            {
                "gewijzigd": gewijzigd,
                "oud": {key: oud[key] for key in gewijzigd},
                "nieuw": {key: nieuw[key] for key in gewijzigd},
                ATTR_JAAR: current[ATTR_JAAR],
            },
        )
