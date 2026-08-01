"""Entidades de hora para programar el temporizador de Twinstar."""
from __future__ import annotations

import logging
from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .ble_client import TwinstarBLEClient
from .const import DEFAULT_END_TIME, DEFAULT_START_TIME, get_device_info
from .schedule import async_send_schedule_command

_LOGGER = logging.getLogger(__name__)


def _parse_time_str(time_str: str, default_val: time) -> time:
    """Parsea una cadena de hora ISO ('HH:MM:SS' o 'HH:MM') a un objeto datetime.time."""
    try:
        parts = time_str.split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    except (ValueError, TypeError, IndexError):
        pass
    return default_val


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Configura las entidades de hora desde una entrada de configuración."""
    runtime_data = entry.runtime_data
    mac_address = runtime_data.mac_address
    ble_client = runtime_data.ble_client

    async_add_entities(
        [
            TwinstarStartTime(mac_address, ble_client),
            TwinstarEndTime(mac_address, ble_client),
        ]
    )


class TwinstarTimeBase(TimeEntity, RestoreEntity):
    """Clase base para entidades Time de Twinstar."""

    def __init__(
        self,
        mac_address: str,
        name: str,
        unique_suffix: str,
        icon: str,
        default_time: str,
        ble_client: TwinstarBLEClient,
    ) -> None:
        self._mac = mac_address
        self._ble_client = ble_client
        self._attr_name = f"Twinstar {name}"
        self._attr_unique_id = f"twinstar_{mac_address}_{unique_suffix}"
        self._attr_icon = icon
        self._default_time_obj = _parse_time_str(default_time, time(9, 0))
        self._value: time = self._default_time_obj

    @property
    def device_info(self) -> DeviceInfo:
        """Retorna información del dispositivo."""
        return get_device_info(self._mac)

    async def async_added_to_hass(self) -> None:
        """Restaura la última hora configurada."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unknown", "unavailable"):
            self._value = _parse_time_str(last_state.state, self._default_time_obj)
            _LOGGER.debug(
                "Memoria restaurada: %s vuelve a %s",
                self._attr_name,
                self._value,
            )

    @property
    def native_value(self) -> time | None:
        """Retorna la hora actual del selector."""
        return self._value

    async def async_set_value(self, value: time) -> None:
        """Actualiza la hora e inyecta la nueva programación por BLE."""
        self._value = value
        self.async_write_ha_state()

        _LOGGER.debug("Nueva hora en %s: %s", self._attr_name, value)
        await async_send_schedule_command(self.hass, self._mac, self._ble_client)


class TwinstarStartTime(TwinstarTimeBase):
    """Selector para la hora de encendido del acuario."""

    def __init__(self, mac_address: str, ble_client: TwinstarBLEClient) -> None:
        super().__init__(
            mac_address=mac_address,
            name="Hora de Encendido",
            unique_suffix="start_time",
            icon="mdi:weather-sunset-up",
            default_time=DEFAULT_START_TIME,
            ble_client=ble_client,
        )


class TwinstarEndTime(TwinstarTimeBase):
    """Selector para la hora de apagado del acuario."""

    def __init__(self, mac_address: str, ble_client: TwinstarBLEClient) -> None:
        super().__init__(
            mac_address=mac_address,
            name="Hora de Apagado",
            unique_suffix="end_time",
            icon="mdi:weather-sunset-down",
            default_time=DEFAULT_END_TIME,
            ble_client=ble_client,
        )
