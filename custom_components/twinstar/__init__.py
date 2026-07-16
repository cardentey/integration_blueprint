"""Inicialización de la integración Twinstar."""
from __future__ import annotations

import logging
import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall

# Registros para buscar entidades por device_id
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, CONF_MAC, PLATFORMS, CMD_ON, CMD_OFF
from .ble_client import TwinstarBLEClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class TwinstarRuntimeData:
    """Datos en memoria compartidos entre plataformas de una misma entrada."""

    mac_address: str
    ble_client: TwinstarBLEClient
    entities: dict[str, Any] = field(default_factory=dict)


TwinstarConfigEntry = ConfigEntry[TwinstarRuntimeData]


def _get_entry_runtime_data(entry: ConfigEntry) -> TwinstarRuntimeData | None:
    """Obtiene runtime_data de forma segura."""
    return getattr(entry, "runtime_data", None)


def _parse_light_on_state(command: str | bytes | bytearray) -> bool | None:
    """Detecta si un comando enciende o apaga la lámpara.

    Reconoce:
      - CMD_ON / CMD_OFF (bytes directos)
      - "on" / "off" (texto)
      - "A<valor>" (brillo: A0 = off, A1+ = on)

    Returns:
        True si enciende, False si apaga, None si no se puede determinar.
    """
    if isinstance(command, (bytes, bytearray)):
        if command == bytes(CMD_ON) or command == CMD_ON:
            return True
        if command == bytes(CMD_OFF) or command == CMD_OFF:
            return False
        try:
            command = command.decode("utf-8", errors="ignore")
        except Exception:
            return None

    if not isinstance(command, str):
        return None

    cleaned = command.strip().lower()

    # Comandos literales "on" / "off"
    if cleaned in ("on", "on\x00"):
        return True
    if cleaned in ("off", "off\x00"):
        return False

    # Comandos de brillo "A<valor>"
    upper = cleaned.upper()
    if upper.startswith("A"):
        try:
            return int(upper[1:]) != 0
        except ValueError:
            return None

    return None


def _get_twinstar_light_entity(hass: HomeAssistant, target_mac: str):
    """Busca la entidad light registrada para una MAC."""
    for loaded_entry in hass.config_entries.async_entries(DOMAIN):
        runtime_data = _get_entry_runtime_data(loaded_entry)
        if runtime_data is None:
            continue
        entity = runtime_data.entities.get(target_mac)
        if entity is not None:
            return entity
    return None


def _get_ble_client_for_mac(hass: HomeAssistant, target_mac: str) -> TwinstarBLEClient | None:
    """Obtiene el ble_client para una MAC determinada."""
    for loaded_entry in hass.config_entries.async_entries(DOMAIN):
        runtime_data = _get_entry_runtime_data(loaded_entry)
        if runtime_data is None:
            continue
        if runtime_data.mac_address == target_mac:
            return runtime_data.ble_client
    return None


def _update_light_state_from_command(hass: HomeAssistant, target_mac: str, command: str) -> None:
    """Actualiza el estado de la entidad light según el comando enviado."""
    entity = _get_twinstar_light_entity(hass, target_mac)
    if entity is None:
        return
    state = _parse_light_on_state(command)
    if state is None:
        return
    entity.set_is_on(state)


def _obtener_mac_destino(hass: HomeAssistant, call_data: dict) -> str | None:
    """Busca la MAC a partir de entity_id, mac explícita o por defecto."""
    target_mac = call_data.get("mac")
    entity_id = call_data.get("entity_id")

    if entity_id:
        ent_reg = er.async_get(hass)
        dev_reg = dr.async_get(hass)
        entity = ent_reg.async_get(entity_id)
        if entity and entity.device_id:
            device = dev_reg.async_get(entity.device_id)
            if device:
                for identifier in device.identifiers:
                    if identifier[0] == DOMAIN:
                        return identifier[1]

    # Si no pasaron MAC ni entity_id, y solo hay 1 lámpara instalada, la usamos
    if not target_mac:
        runtime_entries = [
            runtime_data.mac_address
            for loaded_entry in hass.config_entries.async_entries(DOMAIN)
            if (runtime_data := _get_entry_runtime_data(loaded_entry)) is not None
        ]
        if len(runtime_entries) == 1:
            return runtime_entries[0]

    return target_mac


async def async_setup_services(hass: HomeAssistant) -> None:
    """Registra los servicios de la integración."""
    if hass.services.has_service(DOMAIN, "send_command"):
        return

    async def handle_send_command(call: ServiceCall) -> None:
        """Envía un comando de texto crudo directamente a la lámpara."""
        command = call.data.get("command")
        target_mac = _obtener_mac_destino(hass, call.data)

        if not target_mac:
            _LOGGER.error("Twinstar (send_command): No se encontró la lámpara destino.")
            return

        ble_client_for_target = _get_ble_client_for_mac(hass, target_mac)
        if not ble_client_for_target:
            _LOGGER.error(
                "Twinstar (send_command): No hay cliente BLE para MAC %s", target_mac
            )
            return

        try:
            success = await ble_client_for_target.send_command(command)
            if success:
                _LOGGER.info("Twinstar: Comando '%s' enviado a MAC: %s", command, target_mac)
                _update_light_state_from_command(hass, target_mac, command)
        except Exception as e:
            _LOGGER.error("Error enviando comando a %s: %s", target_mac, e)

    async def handle_send_sequence(call: ServiceCall) -> None:
        """Envía múltiples comandos en una sola conexión BLE."""
        commands = call.data.get("commands", [])
        delay = call.data.get("delay", 1)
        target_mac = _obtener_mac_destino(hass, call.data)

        if not target_mac:
            _LOGGER.error("Twinstar (send_sequence): No se encontró la lámpara destino.")
            return

        ble_client_for_target = _get_ble_client_for_mac(hass, target_mac)
        if not ble_client_for_target:
            _LOGGER.error(
                "Twinstar (send_sequence): No hay cliente BLE para MAC %s", target_mac
            )
            return

        try:
            success = await ble_client_for_target.send_commands(commands, delay=delay)
            if success:
                # Determinar el estado final de la luz a partir del último comando relevante
                last_state = None
                for cmd in commands:
                    parsed = _parse_light_on_state(cmd)
                    if parsed is not None:
                        last_state = parsed
                if last_state is not None:
                    entity = _get_twinstar_light_entity(hass, target_mac)
                    if entity is not None:
                        entity.set_is_on(last_state)
        except Exception as e:
            _LOGGER.error("Error enviando secuencia a %s: %s", target_mac, e)

    hass.services.async_register(DOMAIN, "send_command", handle_send_command)
    hass.services.async_register(DOMAIN, "send_sequence", handle_send_sequence)


async def async_setup_entry(hass: HomeAssistant, entry: TwinstarConfigEntry) -> bool:
    """Configura Twinstar desde una entrada de configuración."""
    mac_address = entry.data.get(CONF_MAC)
    ble_client = TwinstarBLEClient(hass, mac_address)

    entry.runtime_data = TwinstarRuntimeData(
        mac_address=mac_address,
        ble_client=ble_client,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Configuramos los servicios una sola vez
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TwinstarConfigEntry) -> bool:
    """Descarga la integración y limpia servicios si no quedan entradas."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Si no quedan más entradas cargadas, eliminamos los servicios
    remaining = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id and e.state == ConfigEntryState.LOADED
    ]
    if not remaining:
        hass.services.async_remove(DOMAIN, "send_command")
        hass.services.async_remove(DOMAIN, "send_sequence")

    return unload_ok