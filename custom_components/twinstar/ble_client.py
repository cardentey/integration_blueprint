"""Cliente BLE centralizado para Twinstar."""
from __future__ import annotations

import asyncio
import logging

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.core import HomeAssistant

from .const import WRITE_UUID

_LOGGER = logging.getLogger(__name__)


class TwinstarBLEClient:
    """Gestiona la conexión BLE con una lámpara Twinstar.

    Serializa todas las operaciones BLE con un asyncio.Lock() para evitar
    colisiones cuando múltiples automatizaciones envían comandos a la vez.
    """

    def __init__(self, hass: HomeAssistant, mac_address: str) -> None:
        self._hass = hass
        self._mac = mac_address
        self._lock = asyncio.Lock()

    @property
    def mac_address(self) -> str:
        """Retorna la dirección MAC del dispositivo."""
        return self._mac

    async def send_commands(
        self, commands: list[bytes | bytearray | str], delay: float = 0.1
    ) -> bool:
        """Envía una secuencia de comandos BLE en una sola conexión.

        Args:
            commands: Lista de comandos (bytes, bytearray o str).
            delay: Pausa en segundos entre cada comando.

        Returns:
            True si todos los comandos se enviaron correctamente.
        """
        async with self._lock:
            ble_device = async_ble_device_from_address(
                self._hass, self._mac, connectable=True
            )
            if not ble_device:
                _LOGGER.error(
                    "Twinstar (%s) fuera de alcance Bluetooth", self._mac
                )
                return False

            try:
                client = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    f"Twinstar_{self._mac[-5:]}",
                )
                try:
                    for cmd in commands:
                        if isinstance(cmd, str):
                            cmd = cmd.encode("utf-8")
                        await client.write_gatt_char(
                            WRITE_UUID, cmd, response=True
                        )
                        await asyncio.sleep(delay)
                finally:
                    await client.disconnect()
                return True
            except Exception as err:
                _LOGGER.error(
                    "Error BLE Twinstar (%s): %s", self._mac, err
                )
                return False

    async def send_command(self, command: bytes | bytearray | str) -> bool:
        """Envía un solo comando BLE."""
        if isinstance(command, str):
            command = command.encode("utf-8")
        return await self.send_commands([command])
