from __future__ import annotations

from datetime import timedelta

DOMAIN = "cozylife_sensors"

CONF_COUNTRY_CODE = "country_code"

DEFAULT_COUNTRY_CODE = "380"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)

API_BASE_URL = "https://api-us.doiting.com/api"
API_USER_AGENT = "DoHomeX/1.20.4 (iPhone; iOS 17.3.1; Scale/3.00)"

DPID_HUMIDITY = "4"
DPID_TEMPERATURE = "8"
DPID_BATTERY = "9"

PLATFORMS = ["sensor"]
