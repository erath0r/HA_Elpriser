"""Data coordinator for Elpriser."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import statistics
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ElpriserApiClient, ElpriserApiError, PricePoint
from .const import DEFAULT_HISTORY_DAYS, DEFAULT_SCAN_INTERVAL, DOMAIN

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ElpriserData:
    """Coordinator payload."""

    current_price: float | None
    prices_next_24h: list[dict[str, Any]]
    cheapest_hour: dict[str, Any] | None
    most_expensive_hour: dict[str, Any] | None
    forecast_hourly: list[dict[str, Any]]
    forecast_daily: list[dict[str, Any]]
    forecast_average_next_24h: float | None
    forecast_method: str
    last_updated: str


class ElpriserDataUpdateCoordinator(DataUpdateCoordinator[ElpriserData]):
    """Coordinate price fetching and forecasting."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: ElpriserApiClient,
        bidding_zone: str,
        forecast_days: int,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.api = api
        self.bidding_zone = bidding_zone
        self.forecast_days = forecast_days

    async def _async_update_data(self) -> ElpriserData:
        """Fetch data from the upstream API."""
        now = dt_util.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        actual_end = current_hour + timedelta(days=2)
        history_start = current_hour - timedelta(days=DEFAULT_HISTORY_DAYS)
        history_end = current_hour - timedelta(hours=1)

        try:
            actual_prices, history_prices = await self._async_fetch_price_sets(
                current_hour,
                actual_end,
                history_start,
                history_end,
            )
        except ElpriserApiError as err:
            raise UpdateFailed(str(err)) from err

        future_actual = [point for point in actual_prices if point.start >= current_hour]
        next_24 = future_actual[:24]
        current_point = next(
            (point for point in actual_prices if point.start == current_hour),
            next_24[0] if next_24 else None,
        )

        cheapest_hour = min(next_24, key=lambda point: point.price_dkk_kwh, default=None)
        most_expensive_hour = max(
            next_24, key=lambda point: point.price_dkk_kwh, default=None
        )

        forecast_hourly = self._build_hourly_forecast(
            history_prices=history_prices,
            start=current_hour,
            days=self.forecast_days,
        )
        forecast_daily = self._build_daily_forecast(forecast_hourly)
        forecast_average_next_24h = (
            round(
                statistics.fmean(
                    point["price_dkk_kwh"] for point in forecast_hourly[:24]
                ),
                3,
            )
            if forecast_hourly
            else None
        )

        return ElpriserData(
            current_price=current_point.price_dkk_kwh if current_point else None,
            prices_next_24h=[point.as_dict() for point in next_24],
            cheapest_hour=cheapest_hour.as_dict() if cheapest_hour else None,
            most_expensive_hour=(
                most_expensive_hour.as_dict() if most_expensive_hour else None
            ),
            forecast_hourly=forecast_hourly,
            forecast_daily=forecast_daily,
            forecast_average_next_24h=forecast_average_next_24h,
            forecast_method=(
                "Estimated from the last 28 days using matching weekday and hour averages."
            ),
            last_updated=now.isoformat(),
        )

    async def _async_fetch_price_sets(
        self,
        current_hour: datetime,
        actual_end: datetime,
        history_start: datetime,
        history_end: datetime,
    ) -> tuple[list[PricePoint], list[PricePoint]]:
        """Fetch current and historical prices."""
        return await self.hass.async_create_task(
            self._async_gather_prices(current_hour, actual_end, history_start, history_end)
        )

    async def _async_gather_prices(
        self,
        current_hour: datetime,
        actual_end: datetime,
        history_start: datetime,
        history_end: datetime,
    ) -> tuple[list[PricePoint], list[PricePoint]]:
        """Gather prices concurrently."""
        actual_task = self.api.async_get_hourly_prices(
            bidding_zone=self.bidding_zone,
            start=current_hour,
            end=actual_end,
            timezone_name=self.hass.config.time_zone,
        )
        history_task = self.api.async_get_hourly_prices(
            bidding_zone=self.bidding_zone,
            start=history_start,
            end=history_end,
            timezone_name=self.hass.config.time_zone,
        )
        return await asyncio.gather(actual_task, history_task)

    def _build_hourly_forecast(
        self,
        history_prices: list[PricePoint],
        start: datetime,
        days: int,
    ) -> list[dict[str, Any]]:
        """Estimate future prices from matching weekday/hour averages."""
        grouped: dict[tuple[int, int], list[float]] = defaultdict(list)
        fallback: dict[int, list[float]] = defaultdict(list)

        for point in history_prices:
            grouped[(point.start.weekday(), point.start.hour)].append(point.price_dkk_kwh)
            fallback[point.start.hour].append(point.price_dkk_kwh)

        forecast: list[dict[str, Any]] = []
        for offset in range(days * 24):
            target = start + timedelta(hours=offset)
            samples = grouped.get((target.weekday(), target.hour)) or fallback.get(
                target.hour
            )
            if not samples:
                continue

            forecast.append(
                {
                    "start": target.isoformat(),
                    "price_dkk_kwh": round(statistics.fmean(samples), 3),
                    "source": "estimate",
                }
            )

        return forecast

    def _build_daily_forecast(self, hourly_forecast: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Aggregate hourly forecast into daily averages."""
        grouped: dict[str, list[float]] = defaultdict(list)
        for point in hourly_forecast:
            day_key = point["start"][:10]
            grouped[day_key].append(point["price_dkk_kwh"])

        return [
            {
                "date": day_key,
                "average_price_dkk_kwh": round(statistics.fmean(values), 3),
            }
            for day_key, values in sorted(grouped.items())
            if values
        ]
