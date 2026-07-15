"""Config flow para Twinstar."""
from __future__ import annotations

import re

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from .const import CONF_MAC, DOMAIN

MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


class TwinstarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Maneja el flujo de configuración de Twinstar."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Paso inicial cuando el usuario le da a añadir integración."""
        errors = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].strip().upper()

            if not MAC_REGEX.match(mac):
                errors[CONF_MAC] = "invalid_mac"
            else:
                user_input[CONF_MAC] = mac
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Twinstar ({mac})",
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MAC): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    # --- Autodescubrimiento Bluetooth ---

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak):
        """Se activa automáticamente cuando HA detecta la lámpara en el aire."""
        nombre_dispositivo = discovery_info.name or ""

        # Filtro estricto: Si no es exactamente la Pro, lo ignoramos
        if "twinstar light pro" not in nombre_dispositivo.lower():
            return self.async_abort(reason="not_twinstar_pro")

        # Comprobamos si ya lo teníamos instalado
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Guardamos los datos y lanzamos la ventanita
        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        """Muestra la ventanita diciendo: '¡Encontrada! ¿Quieres añadirla?'."""
        if user_input is not None:
            mac = self._discovery_info.address
            nombre_sugerido = self._discovery_info.name or "Acuario Twinstar"

            return self.async_create_entry(
                title=f"{nombre_sugerido} ({mac[-5:]})",
                data={CONF_MAC: mac},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name or "Twinstar",
                "mac": self._discovery_info.address,
            },
        )