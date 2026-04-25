"""Controladores deslizantes para Twinstar (RGBW + Brillo)."""
import logging
from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_MAC

_LOGGER = logging.getLogger(__name__)
WRITE_UUID = "0000dead-0000-1000-8000-00805f9b34fb"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    mac_address = entry.data.get(CONF_MAC)
    
    # Añadimos 'Brillo General' con el prefijo 'A'
    barras = [
        TwinstarColorNumber(mac_address, "Brillo General", "A"),
        TwinstarColorNumber(mac_address, "Rojo", "R"),
        TwinstarColorNumber(mac_address, "Verde", "G"),
        TwinstarColorNumber(mac_address, "Azul", "B"),
        TwinstarColorNumber(mac_address, "Cultivo (Blanco)", "W"),
    ]
    async_add_entities(barras)

class TwinstarColorNumber(NumberEntity, RestoreEntity):
    """Representación de una barra deslizante para Twinstar."""
    def __init__(self, mac_address, name, prefix):
        self._mac = mac_address
        self._prefix = prefix
        self._attr_name = f"Twinstar {name}"
        self._attr_unique_id = f"twinstar_{mac_address}_{prefix}"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._value = 50

    # ¡Añade exactamente el mismo device_info aquí!
    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._mac)},
            name="Acuario Twinstar",
            manufacturer="Twinstar",
            model="Controlador LED Bluetooth",
        )

    # --- NUEVA FUNCIÓN DE MEMORIA ---
    async def async_added_to_hass(self):
        """Restaura el último estado conocido justo antes de arrancar."""
        await super().async_added_to_hass()
        
        # Buscamos en la base de datos de Home Assistant
        last_state = await self.async_get_last_state()
        
        # Si encontramos un estado anterior válido, lo sobreescribimos
        if last_state and last_state.state not in ("unknown", "unavailable"):
            try:
                self._value = int(float(last_state.state))
                _LOGGER.debug("Memoria restaurada: %s vuelve al %s%%", self._attr_name, self._value)
            except ValueError:
                pass # Si por algún motivo la base de datos tiene un error, se queda en el 50 del init
    # --------------------------------

    @property
    def native_value(self):
        return self._value
    
    async def async_set_native_value(self, value: float):
        self._value = int(value)
        comando = f"{self._prefix}{self._value}"
        
        # Buscamos la lámpara en el radar de Home Assistant
        ble_device = async_ble_device_from_address(self.hass, self._mac, connectable=True)
        
        if not ble_device:
            _LOGGER.error("Twinstar (%s) no está al alcance del Bluetooth", self._mac)
            return
            
        try:
            # Conexión anti-fallos y reintentos automáticos
            client = await establish_connection(BleakClientWithServiceCache, ble_device, self._attr_name)
            try:
                await client.write_gatt_char(WRITE_UUID, comando.encode('utf-8'), response=True)
                _LOGGER.debug("Enviado %s con éxito", comando)
            finally:
                await client.disconnect() # Soltamos la conexión al terminar
        except Exception as e:
            _LOGGER.error("Error enviando %s a Twinstar: %s", comando, e)
