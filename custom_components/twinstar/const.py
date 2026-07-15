"""Constantes para la integración Twinstar."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

DOMAIN = "twinstar"
CONF_MAC = "mac_address"

# BLE
WRITE_UUID = "0000dead-0000-1000-8000-00805f9b34fb"
CMD_ON = bytearray.fromhex("6f6e00")
CMD_OFF = bytearray.fromhex("6f666600")

# Canales de color
CHANNEL_BRIGHTNESS = "A"
CHANNEL_RED = "R"
CHANNEL_GREEN = "G"
CHANNEL_BLUE = "B"
CHANNEL_WHITE = "W"

# Plataformas
PLATFORMS: list[str] = ["light", "number"]

# Todos los canales para los sliders number (incluido brillo como meta de rampa)
ALL_CHANNELS: list[tuple[str, str, str]] = [
    (CHANNEL_BRIGHTNESS, "Brillo General", "mdi:brightness-7"),
    (CHANNEL_RED, "Rojo", "mdi:palette"),
    (CHANNEL_GREEN, "Verde", "mdi:palette"),
    (CHANNEL_BLUE, "Azul", "mdi:palette"),
    (CHANNEL_WHITE, "Cultivo (Blanco)", "mdi:white-balance-sunny"),
]

# Solo los canales de color (sin brillo) — para silent_on
COLOR_ONLY_PREFIXES: set[str] = {CHANNEL_RED, CHANNEL_GREEN, CHANNEL_BLUE, CHANNEL_WHITE}


def get_device_info(mac: str) -> DeviceInfo:
    """Genera el DeviceInfo compartido por todas las entidades de un dispositivo."""
    mac_corta = mac[-5:] if mac else "Unknown"
    return DeviceInfo(
        identifiers={(DOMAIN, mac)},
        name=f"Acuario Twinstar ({mac_corta})",
        manufacturer="Twinstar",
        model="Controlador LED Bluetooth",
        sw_version="1.0.0",
    )