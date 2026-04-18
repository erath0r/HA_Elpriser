"""Sensor platform for Elpriser."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ElpriserApiClient
from .const import (
    ATTR_CHEAPEST_HOUR,
    ATTR_FORECAST_DAILY,
    ATTR_FORECAST_DAYS,
    ATTR_FORECAST_HOURLY,
    ATTR_FORECAST_METHOD,
    ATTR_LAST_UPDATED,
    ATTR_MOST_EXPENSIVE_HOUR,
    ATTR_PRICE_NOTE,
    ATTR_PRICES_NEXT_24H,
    ATTR_SOURCE,
    DEFAULT_BIDDING_ZONE,
    DEFAULT_FORECAST_DAYS,
    DOMAIN,
    NAME,
    PRICE_UNIT,
)
from .coordinator import ElpriserDataUpdateCoordinator

CONF_BIDDING_ZONE = "bidding_zone"

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=NAME): cv.string,
        vol.Optional(CONF_BIDDING_ZONE, default=DEFAULT_BIDDING_ZONE): cv.string,
        vol.Optional(ATTR_FORECAST_DAYS, default=DEFAULT_FORECAST_DAYS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=7)
        ),
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the Elpriser sensors from YAML."""
    session = async_get_clientsession(hass)
    api = ElpriserApiClient(session)
    coordinator = ElpriserDataUpdateCoordinator(
        hass=hass,
        api=api,
        bidding_zone=config[CONF_BIDDING_ZONE],
        forecast_days=config[ATTR_FORECAST_DAYS],
    )
    await coordinator.async_refresh()

    base_name = config[CONF_NAME]
    async_add_entities(
        [
            ElpriserCurrentPriceSensor(
                coordinator=coordinator,
                base_name=base_name,
                bidding_zone=config[CONF_BIDDING_ZONE],
            ),
            ElpriserForecastSensor(
                coordinator=coordinator,
                base_name=base_name,
                bidding_zone=config[CONF_BIDDING_ZONE],
            ),
        ]
    )


class ElpriserBaseSensor(CoordinatorEntity[ElpriserDataUpdateCoordinator], SensorEntity):
    """Base sensor for Elpriser entities."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PRICE_UNIT
    _attr_icon = "mdi:lightning-bolt"

    def __init__(
        self,
        coordinator: ElpriserDataUpdateCoordinator,
        base_name: str,
        bidding_zone: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, bidding_zone)},
            "name": f"{base_name} {bidding_zone}",
            "manufacturer": "Energy-Charts",
            "model": "Spot price feed",
        }
        self._attr_unique_id = f"{DOMAIN}_{bidding_zone}_{self.entity_description_key}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return shared state attributes."""
        data = self.coordinator.data
        if data is None:
            return {
                ATTR_SOURCE: "https://api.energy-charts.info/price",
                ATTR_PRICE_NOTE: "Priserne er omregnet fra EUR/MWh til DKK/kWh og er uden nettarif, afgifter og moms.",
            }
        return {
            ATTR_LAST_UPDATED: data.last_updated,
            ATTR_SOURCE: "https://api.energy-charts.info/price",
            ATTR_PRICE_NOTE: "Priserne er omregnet fra EUR/MWh til DKK/kWh og er uden nettarif, afgifter og moms.",
        }


class ElpriserCurrentPriceSensor(ElpriserBaseSensor):
    """Current price sensor with next 24 hours in attributes."""

    entity_description_key = "current_price"
    _attr_name = "Nuvaerende elpris"

    @property
    def native_value(self) -> float | None:
        """Return the current price."""
        data = self.coordinator.data
        return data.current_price if data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return sensor attributes."""
        attributes = super().extra_state_attributes
        data = self.coordinator.data
        if data is None:
            return attributes
        attributes.update(
            {
                ATTR_PRICES_NEXT_24H: data.prices_next_24h,
                ATTR_CHEAPEST_HOUR: data.cheapest_hour,
                ATTR_MOST_EXPENSIVE_HOUR: data.most_expensive_hour,
            }
        )
        return attributes


class ElpriserForecastSensor(ElpriserBaseSensor):
    """Forecast sensor for the next week."""

    entity_description_key = "forecast"
    _attr_name = "Elpris ugeprognose"
    _attr_icon = "mdi:chart-timeline-variant"

    @property
    def native_value(self) -> float | None:
        """Return the average estimated price for the next 24 forecast hours."""
        data = self.coordinator.data
        return data.forecast_average_next_24h if data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return forecast attributes."""
        attributes = super().extra_state_attributes
        data = self.coordinator.data
        if data is None:
            return attributes
        attributes.update(
            {
                ATTR_FORECAST_METHOD: data.forecast_method,
                ATTR_FORECAST_HOURLY: data.forecast_hourly,
                ATTR_FORECAST_DAILY: data.forecast_daily,
            }
        )
        return attributes
