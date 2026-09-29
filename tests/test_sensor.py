"""Tests for setup, sensors and coordinator behaviour."""
from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.evides_tarieven.const import (
    DOMAIN,
    EVENT_TARIEF_GEWIJZIGD,
    ISSUE_PAGINA_GEWIJZIGD,
    TARIEVEN_URL,
)

VASTRECHT = "sensor.evides_tarieven_fixed_annual_charge"
VARIABEL = "sensor.evides_tarieven_variable_rate_per_m3"
BOL = "sensor.evides_tarieven_water_tax_per_m3"
TOTAAL = "sensor.evides_tarieven_total_rate_per_m3"
PER_DAG = "sensor.evides_tarieven_fixed_charge_per_day"
LAATST = "sensor.evides_tarieven_last_checked"


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_sensors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, tarieven_html: str
) -> None:
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html)
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    assert float(hass.states.get(VASTRECHT).state) == 101.05
    assert float(hass.states.get(VARIABEL).state) == 1.32
    assert float(hass.states.get(BOL).state) == 0.476
    assert float(hass.states.get(TOTAAL).state) == pytest.approx(1.796)
    assert float(hass.states.get(PER_DAG).state) == pytest.approx(101.05 / 365, rel=1e-5)
    assert hass.states.get(TOTAAL).attributes["unit_of_measurement"] == "€/m³"
    assert hass.states.get(VASTRECHT).attributes["jaar"] == 2026
    assert dt_util.parse_datetime(hass.states.get(LAATST).state) is not None

    registry = er.async_get(hass)
    assert registry.async_get(LAATST).entity_category == "diagnostic"


async def test_unload(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, tarieven_html: str
) -> None:
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html)
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_not_ready_without_cache(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(TARIEVEN_URL, exc=TimeoutError())
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_keeps_values_on_network_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, tarieven_html: str,
) -> None:
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html)
    entry = await _setup(hass)

    aioclient_mock.clear_requests()
    aioclient_mock.get(TARIEVEN_URL, status=503)
    await _refresh(hass, entry)

    assert float(hass.states.get(VASTRECHT).state) == 101.05


async def test_uses_disk_cache_after_restart(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    hass_storage: dict,
    tarieven_html: str,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={}, entry_id="abc")
    hass_storage[f"{DOMAIN}.abc"] = {
        "version": 1,
        "key": f"{DOMAIN}.abc",
        "data": {
            "values": {"vastrecht": 90.0, "variabel_tarief": 1.2, "belasting_leidingwater": 0.4},
            "jaar": 2025,
            "jaar_bron": "pagina",
            "bron_url": TARIEVEN_URL,
            "laatst_gecontroleerd": "2025-12-01T00:00:00+00:00",
        },
    }
    aioclient_mock.get(TARIEVEN_URL, exc=TimeoutError())
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert float(hass.states.get(VASTRECHT).state) == 90.0


async def test_change_event(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, tarieven_html: str,
) -> None:
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html)
    entry = await _setup(hass)
    events = async_capture_events(hass, EVENT_TARIEF_GEWIJZIGD)

    # Same page again: no event.
    await _refresh(hass, entry)
    assert events == []

    aioclient_mock.clear_requests()
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html.replace("€ 1,320", "€ 1,400"))
    await _refresh(hass, entry)

    assert float(hass.states.get(VARIABEL).state) == 1.4
    assert len(events) == 1
    assert events[0].data == {
        "gewijzigd": ["variabel_tarief"],
        "oud": {"variabel_tarief": 1.32},
        "nieuw": {"variabel_tarief": 1.4},
        "jaar": 2026,
    }


async def test_repair_issue_on_layout_change(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    issue_registry: ir.IssueRegistry,
    tarieven_html: str,
) -> None:
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html.replace("Variabel tarief", "Prijs"))
    entry = await _setup(hass)

    assert hass.states.get(VARIABEL).state == STATE_UNAVAILABLE
    assert hass.states.get(TOTAAL).state == STATE_UNAVAILABLE
    assert float(hass.states.get(VASTRECHT).state) == 101.05
    issue = issue_registry.async_get_issue(DOMAIN, ISSUE_PAGINA_GEWIJZIGD)
    assert issue is not None
    assert issue.translation_placeholders["ontbrekend"] == "Variabel tarief"

    # Page fixed again: the issue disappears.
    aioclient_mock.clear_requests()
    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html)
    await _refresh(hass, entry)
    assert issue_registry.async_get_issue(DOMAIN, ISSUE_PAGINA_GEWIJZIGD) is None
    assert float(hass.states.get(VARIABEL).state) == 1.32


async def test_repair_issue_when_nothing_found(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    issue_registry: ir.IssueRegistry,
) -> None:
    aioclient_mock.get(TARIEVEN_URL, text="<html><body>Onderhoud</body></html>")
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert issue_registry.async_get_issue(DOMAIN, ISSUE_PAGINA_GEWIJZIGD) is not None


async def test_diagnostics(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, tarieven_html: str
) -> None:
    from custom_components.evides_tarieven.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    aioclient_mock.get(TARIEVEN_URL, text=tarieven_html)
    entry = await _setup(hass)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["last_update_success"] is True
    assert diag["data"]["values"]["vastrecht"] == 101.05
