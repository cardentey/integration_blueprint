"""Interruptor inteligente para Twinstar."""
import logging
import asyncio

from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_platform # <-- IMPORTANTE PARA EL NUEVO SERVICIO

from .const import DOMAIN, CONF_MAC

_LOGGER = logging.getLogger(__name__)
WRITE_UUID = "0000dead-0000-1000-8000-00805f9b34fb"
CMD_ON = bytearray.fromhex("6f6e00")
CMD_OFF = bytearray.fromhex("6f666600")

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    mac_address = entry.data.get(CONF_MAC)
    async_add_entities([TwinstarLight(mac_address)], update_before_add=True)

    # --- REGISTRAMOS EL SERVICIO EXCLUSIVO DE ESTA LUZ ---
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "silent_on",
        {}, # No necesita parámetros extra, coge todo de la base de datos
        "async_silent_on",
    )

class TwinstarLight(LightEntity):
    def __init__(self, mac_address):
        self._mac = mac_address
        self._attr_name = "Acuario Twinstar"
        self._attr_unique_id = f"twinstar_light_{mac_address}"
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self._attr_icon = "mdi:lightbulb-fluorescent-tube"
        self._is_on = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac)},
            name="Acuario Twinstar",
            manufacturer="Twinstar",
            model="Controlador LED Bluetooth",
            sw_version="1.0 (Hackeado)",
        )

    @property
    def is_on(self):
        return self._is_on

    async def _send_robust_commands(self, comandos_list):
        ble_device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        if not ble_device:
            _LOGGER.error("Twinstar (%s) no está al alcance del Bluetooth", self._mac)
            return

        try:
            client = await establish_connection(BleakClientWithServiceCache, ble_device, self._attr_name)
            try:
                for comando in comandos_list:
                    await client.write_gatt_char(WRITE_UUID, comando, response=True)
                    await asyncio.sleep(0.1)
            finally:
                await client.disconnect()
        except Exception as e:
            _LOGGER.error("Error en conexión con Twinstar: %s", e)

    async def async_turn_on(self, **kwargs):
        """Encendido normal desde el botón (RESTAURAMOS LA 'A' AQUÍ)"""
        entidades = [
            ("A", "number.twinstar_brillo_general"), # Vuelve la A para que funcione normal
            ("R", "number.twinstar_rojo"),
            ("G", "number.twinstar_verde"),
            ("B", "number.twinstar_azul"),
            ("W", "number.twinstar_cultivo_blanco"),
        ]

        comandos_a_enviar = []
        for prefix, entity_id in entidades:
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable"):
                val = int(float(state.state))
                comandos_a_enviar.append(f"{prefix}{val}".encode('utf-8'))
        
        comandos_a_enviar.append(CMD_ON)
        await self._send_robust_commands(comandos_a_enviar)
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        """Apaga la luz de forma segura."""
        await self._send_robust_commands([CMD_OFF])
        self._is_on = False

    # --- LA NUEVA FUNCIÓN PARA EL AMANECER ---
    async def async_silent_on(self):
        """Prepara la rampa: Manda A0, inyecta colores y da el ON en una sola conexión."""
        comandos_a_enviar = ["A1".encode('utf-8')] # Obligamos al brillo a ser 0
        
        entidades_color = [
            ("R", "number.twinstar_rojo"),
            ("G", "number.twinstar_verde"),
            ("B", "number.twinstar_azul"),
            ("W", "number.twinstar_cultivo_blanco"),
        ]

        for prefix, entity_id in entidades_color:
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable"):
                val = int(float(state.state))
                comandos_a_enviar.append(f"{prefix}{val}".encode('utf-8'))
        
        comandos_a_enviar.append(CMD_ON) # Rematamos con el encendido
        
        # Enviamos TODA la secuencia en un solo bloque sin atascar el Bluetooth
        await self._send_robust_commands(comandos_a_enviar)
        
        self._is_on = True
        self.async_write_ha_state() # Actualizamos el botón de Home Assistant a amarillo