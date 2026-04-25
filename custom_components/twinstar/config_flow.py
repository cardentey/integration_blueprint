"""Config flow para Twinstar."""
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_MAC

class TwinstarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Maneja el flujo de configuración de Twinstar."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Paso inicial cuando el usuario le da a añadir integración."""
        errors = {}

        if user_input is not None:
            # Si el usuario ha rellenado la MAC y le ha dado a Enviar:
            return self.async_create_entry(
                title=f"Twinstar ({user_input[CONF_MAC]})", 
                data=user_input
            )

        # Si es la primera vez que se abre la ventana, dibujamos el formulario:
        data_schema = vol.Schema({
            vol.Required(CONF_MAC, default="50:78:7D:4C:1A:FA"): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
    
    # --- 2. EL RADAR (Autodescubrimiento Bluetooth) ---
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
            # Si el usuario le da a enviar, creamos el dispositivo automáticamente
            mac = self._discovery_info.address
            nombre_sugerido = self._discovery_info.name or "Acuario Twinstar"
            
            return self.async_create_entry(
                title=f"{nombre_sugerido} ({mac[-5:]})",
                data={CONF_MAC: mac}
            )

        # Si aún no le ha dado, le mostramos el formulario con el botón
        self._set_confirm_only() # Esto hace que el formulario solo tenga el botón de Enviar (sin campos de texto)
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name or "Twinstar",
                "mac": self._discovery_info.address
            }
        )