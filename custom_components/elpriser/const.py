"""Constants for the Elpriser integration."""

from datetime import timedelta

DOMAIN = "elpriser"
NAME = "Elpriser"
PRICE_UNIT = "DKK/kWh"
EUR_TO_DKK = 7.46
MWH_TO_KWH = 1000
ATTR_FORECAST_DAYS = "forecast_days"
ATTR_PRICES_NEXT_24H = "prices_next_24h"
ATTR_FORECAST_HOURLY = "forecast_hourly"
ATTR_FORECAST_DAILY = "forecast_daily"
ATTR_CHEAPEST_HOUR = "cheapest_hour"
ATTR_MOST_EXPENSIVE_HOUR = "most_expensive_hour"
ATTR_LAST_UPDATED = "last_updated"
ATTR_FORECAST_METHOD = "forecast_method"
ATTR_SOURCE = "source"
ATTR_PRICE_NOTE = "price_note"
DEFAULT_BIDDING_ZONE = "DK1"
DEFAULT_FORECAST_DAYS = 7
DEFAULT_HISTORY_DAYS = 28
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
API_BASE_URL = "https://api.energy-charts.info"
