"""Inicialización de la integración Twinstar."""
import logging
import asyncio

from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# --- NUEVOS IMPORTS PARA BUSCAR ENTIDADES ---
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr
# --------------------------------------------

from .const import DOMAIN, CONF_MAC

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["light", "number"]
WRITE_UUID = "0000dead-0000-1000-8000-00805f9b34fb"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura Twinstar desde una entrada de configuración."""
    hass.data.setdefault(DOMAIN, {})
    mac_address = entry.data.get(CONF_MAC)

    # 1. Guardamos la MAC de esta lámpara en el diccionario global
    hass.data[DOMAIN][entry.entry_id] = mac_address

    # 2. Cargamos las plataformas
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # --- FUNCIÓN AYUDANTE PARA TRADUCIR ENTIDAD A MAC ---
    def _obtener_mac_destino(call_data):
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
        if not target_mac and len(hass.data[DOMAIN]) == 1:
            return list(hass.data[DOMAIN].values())[0]

        return target_mac
    # ----------------------------------------------------

    async def handle_send_command(call):
        """Envía un comando de texto crudo directamente a la lámpara de forma segura."""
        command = call.data.get("command")
        target_mac = _obtener_mac_destino(call.data)

        if not target_mac:
            _LOGGER.error("Twinstar (send_command): Falta entity_id o no se encontró la lámpara.")
            return

        ble_device = async_ble_device_from_address(hass, target_mac, connectable=True)
        
        if not ble_device:
            _LOGGER.error("Twinstar (send_command): Dispositivo (%s) fuera de rango", target_mac)
            return

        try:
            client = await establish_connection(BleakClientWithServiceCache, ble_device, "Twinstar_Service")
            try:
                await client.write_gatt_char(WRITE_UUID, command.encode('utf-8'), response=True)
                _LOGGER.info("Twinstar: Comando '%s' enviado a MAC: %s", command, target_mac)
            finally:
                await client.disconnect()
        except Exception as e:
            _LOGGER.error("Error en Twinstar enviando comando %s: %s", command, e)

    async def handle_send_sequence(call):
        """Envía múltiples comandos en una sola conexión BLE."""
        commands = call.data.get("commands", [])
        delay = call.data.get("delay", 1)
        target_mac = _obtener_mac_destino(call.data)

        if not target_mac:
            _LOGGER.error("Twinstar (send_sequence): Falta entity_id o no se encontró la lámpara.")
            return

        ble_device = async_ble_device_from_address(hass, target_mac, connectable=True)

        if not ble_device:
            _LOGGER.error("Twinstar (send_sequence): Dispositivo (%s) fuera de rango", target_mac)
            return

        try:
            client = await establish_connection(BleakClientWithServiceCache, ble_device, "Twinstar_Service")
            try:
                for cmd in commands:
                    await client.write_gatt_char(WRITE_UUID, cmd.encode("utf-8"), response=True)
                    _LOGGER.debug("Secuencia Twinstar: Comando enviado %s", cmd)
                    await asyncio.sleep(delay)
            finally:
                await client.disconnect()
        except Exception as e:
            _LOGGER.error("Error en secuencia Twinstar: %s", e)

    # 3. Registramos los servicios SOLO si no se han registrado antes 
    # (Para no sobrescribirlos al añadir una 2ª lámpara)
    if not hass.services.has_service(DOMAIN, "send_command"):
        hass.services.async_register(DOMAIN, "send_command", handle_send_command)
    if not hass.services.has_service(DOMAIN, "send_sequence"):
        hass.services.async_register(DOMAIN, "send_sequence", handle_send_sequence)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descarga la integración si decides borrarla."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok