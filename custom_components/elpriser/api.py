"""API client for electricity price data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import statistics
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.util import dt as dt_util

from .const import API_BASE_URL, EUR_TO_DKK, MWH_TO_KWH


class ElpriserApiError(Exception):
    """Raised when the API request fails."""


@dataclass(slots=True)
class PricePoint:
    """Normalized hourly price point."""

    start: datetime
    price_dkk_kwh: float

    def as_dict(self) -> dict[str, Any]:
        """Convert the point into a Home Assistant-friendly dict."""
        return {
            "start": self.start.isoformat(),
            "price_dkk_kwh": self.price_dkk_kwh,
        }


class ElpriserApiClient:
    """Fetch and normalize price data from Energy-Charts."""

    def __init__(self, session: ClientSession) -> None:
        """Initialize the client."""
        self._session = session

    async def async_get_hourly_prices(
        self,
        bidding_zone: str,
        start: datetime,
        end: datetime,
        timezone_name: str,
    ) -> list[PricePoint]:
        """Return hourly mean prices for the requested interval."""
        params = {
            "bzn": bidding_zone,
            "start": start.date().isoformat(),
            "end": end.date().isoformat(),
        }

        try:
            async with self._session.get(
                f"{API_BASE_URL}/price",
                params=params,
                timeout=30,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        except (TimeoutError, ClientError, ValueError) as err:
            raise ElpriserApiError(f"Could not fetch prices: {err}") from err

        raw_timestamps = payload.get("unix_seconds", [])
        raw_prices = payload.get("price", [])

        if len(raw_timestamps) != len(raw_prices):
            raise ElpriserApiError("Unexpected response shape from price API")

        timezone = dt_util.get_time_zone(timezone_name) or dt_util.UTC
        buckets: dict[datetime, list[float]] = defaultdict(list)

        for unix_seconds, price in zip(raw_timestamps, raw_prices, strict=True):
            if price is None:
                continue

            local_dt = datetime.fromtimestamp(unix_seconds, tz=dt_util.UTC).astimezone(
                timezone
            )
            hour_start = local_dt.replace(minute=0, second=0, microsecond=0)
            buckets[hour_start].append(float(price))

        points = [
            PricePoint(
                start=hour_start,
                price_dkk_kwh=round(
                    (statistics.fmean(values) * EUR_TO_DKK) / MWH_TO_KWH,
                    3,
                ),
            )
            for hour_start, values in buckets.items()
            if values
        ]
        points.sort(key=lambda point: point.start)

        return [point for point in points if start <= point.start <= end]
