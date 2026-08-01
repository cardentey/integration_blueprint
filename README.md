# Twinstar Aquarium Light for Home Assistant

![Home Assistant Dashboard](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)
![Bluetooth](https://img.shields.io/badge/Connectivity-Bluetooth%20BLE-informational.svg)
![Model](https://img.shields.io/badge/Model-Twinstar%20Light%20Pro-green.svg)

Esta integración personalizada permite controlar las pantallas LED **Twinstar Light Pro (RGBW)** directamente desde Home Assistant mediante Bluetooth (BLE).

## ✨ Características

* **Autodescubrimiento Bluetooth:** La integración detecta automáticamente nuevas lámparas Twinstar Light Pro en el área.
* **Soporte Multi-dispositivo:** Configura y controla múltiples acuarios de forma independiente.
* **Control de Canales Individuales:** Entidades `number` para ajustar Rojo, Verde, Azul, Blanco y Brillo General (0-100%).
* **Temporizador en Hardware (Horarios y Rampas):** Entidades nativas de hora (`time`) y deslizadores para programar el amanecer/atardecer directamente en la memoria del controlador (`TOn:HHMM_HHMM_MM_MM`).
* **Sincronización de Reloj al Segundo:** Sincronización automática de fecha y hora (`YYYYMMDDHHMMSS`) del controlador en cada ajuste y botón manual (`button.twinstar_sincronizar_reloj`).
* **Persistencia de Estado:** Los valores de los canales y duraciones se restauran automáticamente tras reiniciar Home Assistant.
* **Servicios Avanzados:**
    * `set_schedule`: Programa encendido, apagado y duraciones de rampa en un solo paso.
    * `send_command`: Envío de comandos crudos.
    * `send_sequence`: Ráfagas de comandos con retardos (ideal para efectos).
* **Conexión Blindada:** Implementación de `bleak-retry-connector` para evitar desconexiones y errores de emparejamiento.

---

## 🛠️ Instalación

### Método Manual
1. Descarga el contenido de la carpeta `/custom_components/twinstar`.
2. Cópialo en tu directorio de Home Assistant: `/config/custom_components/twinstar`.
3. Reinicia Home Assistant.

---

## ⚙️ Configuración

### Autodescubrimiento
Si tu Home Assistant tiene un adaptador Bluetooth o un **ESPHome Bluetooth Proxy**, aparecerá una notificación de "Nuevo dispositivo descubierto" automáticamente cuando la lámpara esté en modo emparejamiento.

### Configuración Manual
Si no aparece el descubrimiento:
1. Ve a **Ajustes** -> **Dispositivos y servicios**.
2. Haz clic en **Añadir integración**.
3. Busca **Twinstar**.
4. Introduce la dirección MAC de tu lámpara.

---

## ⏱️ Programación Nativa en el Controlador

La integración permite actuar directamente sobre el temporizador y el reloj en tiempo real (RTC) del controlador LED Twinstar sin necesidad de scripts continuos en Home Assistant:
- **Hora de Encendido / Hora de Apagado (`time`):** Entidades nativas con selector de hora para fijar el horario diario de luz.
- **Amanecer / Atardecer (`number`):** Deslizadores de 0 a 60 minutos para configurar la rampa de encendido progresivo y apagado suave.
- **Resiliencia ante Cortes Eléctricos:** Monitoreo activo de la señal BLE. Tras un reinicio de Home Assistant o un corte de luz (>60 segundos), la integración detecta la reconexión y resincroniza automáticamente la hora RTC, la programación de horario y los registros de color RGBW y Brillo en la memoria del controlador (manteniendo la pantalla apagada si era de noche o encendiéndola si estaba activa).



---

## 💡 Servicios (Actions)

### `twinstar.set_schedule`
Programa la hora de encendido, apagado y duraciones de rampa en el controlador.
* `entity_id`: La lámpara destino.
* `start_time`: Hora de encendido (ej: `09:00`).
* `end_time`: Hora de apagado (ej: `21:00`).
* `sunrise_minutes`: Minutos de amanecer (rango 0-60).
* `sunset_minutes`: Minutos de atardecer (rango 0-60).

### `twinstar.send_command`
Envía un comando único (ej: `A50` para brillo al 50%).
* `entity_id`: La lámpara destino.
* `command`: El comando de texto.

---

## ⚠️ Disclaimer
Esta integración no es oficial de Twinstar. Ha sido desarrollada mediante ingeniería inversa para la comunidad de acuarofilia. Úsala bajo tu propia responsabilidad.

---
**Desarrollado con ❤️ para los amantes de los acuarios plantados.**

