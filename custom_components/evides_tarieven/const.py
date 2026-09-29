"""Constants for the Evides Tarieven integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "evides_tarieven"

TARIEVEN_URL = "https://www.evides.nl/service/tarieven"

# Data keys scraped from the page (also used as unique_id suffixes)
KEY_VASTRECHT = "vastrecht"
KEY_VARIABEL_TARIEF = "variabel_tarief"
KEY_BELASTING_LEIDINGWATER = "belasting_leidingwater"
SCRAPED_KEYS = (KEY_VASTRECHT, KEY_VARIABEL_TARIEF, KEY_BELASTING_LEIDINGWATER)

# Derived sensor keys
KEY_TOTAAL_PER_M3 = "totaal_per_m3"
KEY_VASTRECHT_PER_DAG = "vastrecht_per_dag"
KEY_LAATST_GECONTROLEERD = "laatst_gecontroleerd"

ATTR_JAAR = "jaar"
ATTR_JAAR_BRON = "jaar_bron"
ATTR_BRON_URL = "bron_url"
ATTR_LAATST_GECONTROLEERD = "laatst_gecontroleerd"

CONF_SCAN_INTERVAL_HOURS = "scan_interval_hours"
DEFAULT_SCAN_INTERVAL_HOURS = 24
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 24 * 30  # 30 days

DEFAULT_UPDATE_INTERVAL = timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS)

REQUEST_TIMEOUT_SECONDS = 30

# Fired on the event bus when a scraped tariff differs from the previous value.
EVENT_TARIEF_GEWIJZIGD = f"{DOMAIN}_tarief_gewijzigd"

# Repair issue raised when the page no longer contains (all) expected rows.
ISSUE_PAGINA_GEWIJZIGD = "pagina_gewijzigd"
