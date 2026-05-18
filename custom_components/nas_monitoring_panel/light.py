from __future__ import annotations

from datetime import timedelta
from typing import Any
import logging

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EspNasMonitorApi
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEFAULT_BRIGHTNESS,
    DEFAULT_LIGHT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def percent_to_ha(value: int) -> int:
    value = max(0, min(100, int(value)))
    return round(value * 255 / 100)


def ha_to_percent(value: int | None) -> int:
    if value is None:
        return DEFAULT_BRIGHTNESS
    value = max(0, min(255, int(value)))
    return round(value * 100 / 255)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NAS Monitoring Panel light."""
    data = entry.data
    session = async_get_clientsession(hass)

    api = EspNasMonitorApi(
        session=session,
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data.get(CONF_USERNAME),
        password=data.get(CONF_PASSWORD),
    )

    coordinator = NasMonitoringPanelCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([NasMonitoringPanelLight(entry, coordinator, api)])


class NasMonitoringPanelCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for display status polling."""

    def __init__(self, hass: HomeAssistant, api: EspNasMonitorApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_light",
            update_interval=timedelta(seconds=15),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.status()
        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc


class NasMonitoringPanelLight(LightEntity):
    """Light entity for NAS Monitoring Panel screen brightness."""

    _attr_name = DEFAULT_LIGHT_NAME
    _attr_icon = "mdi:brightness-6"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: NasMonitoringPanelCoordinator,
        api: EspNasMonitorApi,
    ) -> None:
        self._entry = entry
        self._coordinator = coordinator
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_light"

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def is_on(self) -> bool | None:
        data = self._coordinator.data or {}
        power = data.get("power")
        if isinstance(power, bool):
            return power
        state = str(data.get("state", "")).lower()
        if state in ("on", "true", "1"):
            return True
        if state in ("off", "false", "0"):
            return False
        return None

    @property
    def brightness(self) -> int | None:
        data = self._coordinator.data or {}
        brightness = data.get("brightness")
        if brightness is None:
            brightness = data.get("brightness_percent", DEFAULT_BRIGHTNESS)
        try:
            return percent_to_ha(int(brightness))
        except (TypeError, ValueError):
            return percent_to_ha(DEFAULT_BRIGHTNESS)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._coordinator.data or {}
        brightness = data.get("brightness")
        if brightness is None:
            brightness = data.get("brightness_percent", DEFAULT_BRIGHTNESS)
        return {
            "brightness_percent": brightness,
            "schedule_enabled": data.get("schedule_enabled"),
            "on_time": data.get("on_time"),
            "off_time": data.get("off_time"),
            "raw_state": data.get("state"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if not self.is_on:
            await self._api.turn_on()
        if brightness is not None:
            await self._api.set_brightness(ha_to_percent(brightness))
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.turn_off()
        await self._coordinator.async_request_refresh()

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
