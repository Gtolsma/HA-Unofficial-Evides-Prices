"""Constants for the Evides Tarieven integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "evides_tarieven"

TARIEVEN_URL = "https://www.evides.nl/service/tarieven"

# Data keys (also used as sensor object_id suffixes)
KEY_VASTRECHT = "vastrecht"
KEY_VARIABEL_TARIEF = "variabel_tarief"
KEY_BELASTING_LEIDINGWATER = "belasting_leidingwater"

ATTR_JAAR = "jaar"
ATTR_JAAR_BRON = "jaar_bron"
ATTR_BRON_URL = "bron_url"
ATTR_LAATST_GECONTROLEERD = "laatst_gecontroleerd"

CONF_SCAN_INTERVAL_HOURS = "scan_interval_hours"
DEFAULT_SCAN_INTERVAL_HOURS = 24
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 24 * 30  # 30 days

DEFAULT_UPDATE_INTERVAL = timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS)
