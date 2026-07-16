"""Controladores deslizantes para Twinstar (RGBW + Brillo)."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .ble_client import TwinstarBLEClient
from .const import ALL_CHANNELS, CONF_MAC, get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Configura las entidades number desde una entrada de configuración."""
    runtime_data = entry.runtime_data
    mac_address = runtime_data.mac_address
    ble_client = runtime_data.ble_client

    barras = [
        TwinstarColorNumber(mac_address, name, prefix, icon, ble_client)
        for prefix, name, icon in ALL_CHANNELS
    ]
    async_add_entities(barras)


class TwinstarColorNumber(NumberEntity, RestoreEntity):
    """Representación de una barra deslizante para un canal de la Twinstar."""

    def __init__(
        self,
        mac_address: str,
        name: str,
        prefix: str,
        icon: str,
        ble_client: TwinstarBLEClient,
    ) -> None:
        self._mac = mac_address
        self._prefix = prefix
        self._ble_client = ble_client
        self._attr_name = f"Twinstar {name}"
        self._attr_unique_id = f"twinstar_{mac_address}_{prefix}"
        self._attr_icon = icon
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._value = 50

    @property
    def device_info(self) -> DeviceInfo:
        """Retorna información del dispositivo (compartida con light.py)."""
        return get_device_info(self._mac)

    async def async_added_to_hass(self) -> None:
        """Restaura el último estado conocido justo antes de arrancar."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unknown", "unavailable"):
            try:
                self._value = int(float(last_state.state))
                _LOGGER.debug(
                    "Memoria restaurada: %s vuelve al %s%%",
                    self._attr_name,
                    self._value,
                )
            except ValueError:
                pass

    @property
    def native_value(self) -> int:
        """Retorna el valor actual del slider."""
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        """Envía el nuevo valor al dispositivo por BLE."""
        nuevo_valor = int(value)
        comando = f"{self._prefix}{nuevo_valor}"

        success = await self._ble_client.send_command(comando)
        if success:
            self._value = nuevo_valor
            self.async_write_ha_state()
            _LOGGER.debug("Enviado %s con éxito", comando)
        else:
            # Si falla, forzamos a la UI a volver al valor anterior
            self.async_write_ha_state()
