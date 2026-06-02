from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE_URL,
    API_USER_AGENT,
    DEFAULT_COUNTRY_CODE,
    DPID_BATTERY,
    DPID_HUMIDITY,
    DPID_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


class CozyLifeError(Exception):
    """Base CozyLife API error."""


class CozyLifeAuthError(CozyLifeError):
    """CozyLife authentication error."""


@dataclass(slots=True)
class CozyLifeDevice:
    """CozyLife device metadata."""

    id: str
    name: str
    product_id: str | None
    model_name: str | None
    firmware_chip: str | None
    firmware_version: str | None
    online: bool


@dataclass(slots=True)
class CozyLifeDeviceState:
    """CozyLife device state."""

    device: CozyLifeDevice
    temperature: float | None
    humidity: int | None
    battery: float | None
    online: bool
    diagnostics: dict[str, Any]
    raw: dict[str, Any]


class CozyLifeClient:
    """Small async client for the CozyLife cloud API."""

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        country_code: str = DEFAULT_COUNTRY_CODE,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._country_code = country_code
        self._token: str | None = None
        self.devices: dict[str, CozyLifeDevice] = {}

    async def async_login(self) -> None:
        """Log in and store the session token."""
        result = await self._request(
            "POST",
            "/app/user/login",
            json={
                "mail": self._email,
                "passwd": self._password,
                "lang": "en",
                "platform": "ios",
                "imei": "354627900145865",
                "lat": "41.9",
                "lng": "12.5",
                "country_number_code": self._country_code,
                "package_name": "am.doit.cozylife",
                "user_term_version": "1.0.1",
                "user_privacy_version": "1.0.0",
                "package_version": "1.20.4",
            },
            auth=False,
        )

        if result.get("ret") != "1" or not result.get("info", {}).get("token"):
            description = result.get("desc") or "Unknown login error"
            raise CozyLifeAuthError(description)

        self._token = result["info"]["token"]

    async def async_update_devices(self) -> dict[str, CozyLifeDeviceState]:
        """Fetch devices and their current states."""
        if not self._token:
            await self.async_login()

        await self._async_fetch_devices()
        return await self._async_fetch_states()

    async def _async_fetch_devices(self) -> None:
        result = await self._request(
            "GET",
            "/v2/app/device_with_group/list",
            params={"count": 10000, "page": 1},
        )

        if result.get("ret") != "1":
            raise CozyLifeError(result.get("desc") or "Cannot obtain devices")

        devices = result.get("info", {}).get("device_bind", {}).get("list", [])
        parsed: dict[str, CozyLifeDevice] = {}

        for item in devices:
            device_id = item.get("device_id")
            if not device_id:
                continue

            parsed[device_id] = CozyLifeDevice(
                id=device_id,
                name=item.get("device_name") or "CozyLife sensor",
                product_id=item.get("device_product_id"),
                model_name=item.get("device_model_name"),
                firmware_chip=item.get("firmware_chip"),
                firmware_version=item.get("firmware_version"),
                online=bool(item.get("is_online")),
            )

        self.devices = parsed

    async def _async_fetch_states(self) -> dict[str, CozyLifeDeviceState]:
        device_ids = list(self.devices)
        if not device_ids:
            return {}

        result = await self._request(
            "GET",
            "/app/v2/device/states",
            params={"device_ids[]": device_ids},
        )

        if result.get("ret") != "1":
            raise CozyLifeError(result.get("desc") or "Cannot obtain states")

        states: dict[str, CozyLifeDeviceState] = {}
        for item in result.get("info", []):
            device_id = item.get("device_id")
            raw_state = item.get("state") or {}
            device = self.devices.get(device_id)
            if not device or not _looks_like_temperature_sensor(raw_state):
                continue

            states[device_id] = CozyLifeDeviceState(
                device=device,
                temperature=_as_float(raw_state.get(DPID_TEMPERATURE), divisor=10),
                humidity=_as_int(raw_state.get(DPID_HUMIDITY)),
                battery=_as_float(raw_state.get(DPID_BATTERY), divisor=10),
                online=bool(raw_state.get("online", device.online)),
                diagnostics=_decode_diagnostics(raw_state),
                raw=raw_state,
            )

        return states

    async def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_params = dict(params or {})
        if auth:
            if not self._token:
                raise CozyLifeAuthError("Missing token")
            request_params["token"] = self._token

        try:
            response = await self._session.request(
                method,
                f"{API_BASE_URL}{path}",
                params=request_params,
                json=json,
                headers={"user-agent": API_USER_AGENT},
                timeout=20,
            )
            data = await response.json(content_type=None)
        except ClientError as err:
            raise CozyLifeError(f"Connection error: {err}") from err
        except TimeoutError as err:
            raise CozyLifeError("Request timed out") from err

        if response.status >= 400:
            raise CozyLifeError(f"HTTP {response.status}: {data}")

        _LOGGER.debug("CozyLife %s %s response: %s", method, path, data)
        return data


def _looks_like_temperature_sensor(raw_state: dict[str, Any]) -> bool:
    return DPID_TEMPERATURE in raw_state or DPID_HUMIDITY in raw_state


def _decode_diagnostics(raw_state: dict[str, Any]) -> dict[str, Any]:
    """Decode known non-sensitive CozyLife datapoints."""
    diagnostics: dict[str, Any] = {}

    if (value := _as_int(raw_state.get("14"))) is not None:
        diagnostics["report_interval_seconds"] = value

    if (value := _as_float(raw_state.get("20"), divisor=10)) is not None:
        diagnostics["temperature_high_threshold_c"] = value

    if (value := _as_float(raw_state.get("21"), divisor=10)) is not None:
        diagnostics["temperature_low_threshold_c"] = value

    if (value := _as_int(raw_state.get("22"))) is not None:
        diagnostics["humidity_high_threshold"] = value

    if (value := _as_int(raw_state.get("23"))) is not None:
        diagnostics["humidity_low_threshold"] = value

    if (value := _as_float(raw_state.get("24"), divisor=10)) is not None:
        diagnostics["temperature_report_delta_c"] = value

    if (value := _as_int(raw_state.get("25"))) is not None:
        diagnostics["humidity_report_delta"] = value

    if (value := _as_int(raw_state.get("12"))) is not None:
        diagnostics["datapoint_12"] = value

    if (value := _as_int(raw_state.get("13"))) is not None:
        diagnostics["datapoint_13"] = value

    if (value := _as_int(raw_state.get("26"))) is not None:
        diagnostics["datapoint_26"] = value

    if (value := raw_state.get("sn")) is not None:
        diagnostics["last_report_serial"] = str(value)

    return diagnostics


def _as_float(value: Any, divisor: int = 1) -> float | None:
    try:
        return float(value) / divisor
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
