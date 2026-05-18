from __future__ import annotations

from datetime import timedelta
from typing import Any
import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
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
    DEFAULT_TV_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NAS Monitoring Panel TV entity."""
    data = entry.data
    session = async_get_clientsession(hass)

    api = EspNasMonitorApi(
        session=session,
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data.get(CONF_USERNAME),
        password=data.get(CONF_PASSWORD),
    )

    coordinator = NasMonitoringPanelTvCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([NasMonitoringPanelTv(entry, coordinator, api)])


class NasMonitoringPanelTvCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for TV power polling."""

    def __init__(self, hass: HomeAssistant, api: EspNasMonitorApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_tv",
            update_interval=timedelta(seconds=15),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.status()
        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc


class NasMonitoringPanelTv(MediaPlayerEntity):
    """TV-style media player entity for NAS Monitoring Panel."""

    _attr_name = DEFAULT_TV_NAME
    _attr_icon = "mdi:television"
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON | MediaPlayerEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: NasMonitoringPanelTvCoordinator,
        api: EspNasMonitorApi,
    ) -> None:
        self._entry = entry
        self._coordinator = coordinator
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_tv"

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def state(self) -> MediaPlayerState | None:
        data = self._coordinator.data or {}
        power = data.get("power")
        if isinstance(power, bool):
            return MediaPlayerState.ON if power else MediaPlayerState.OFF
        state = str(data.get("state", "")).lower()
        if state in ("on", "true", "1"):
            return MediaPlayerState.ON
        if state in ("off", "false", "0"):
            return MediaPlayerState.OFF
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._coordinator.data or {}
        return {
            "schedule_enabled": data.get("schedule_enabled"),
            "on_time": data.get("on_time"),
            "off_time": data.get("off_time"),
            "raw_state": data.get("state"),
        }

    async def async_turn_on(self) -> None:
        await self._api.turn_on()
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._api.turn_off()
        await self._coordinator.async_request_refresh()

    async def async_update(self) -> None:
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )
