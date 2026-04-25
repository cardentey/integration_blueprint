# Twinstar Aquarium Light for Home Assistant

![Home Assistant Dashboard](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)
![Bluetooth](https://img.shields.io/badge/Connectivity-Bluetooth%20BLE-informational.svg)
![Model](https://img.shields.io/badge/Model-Twinstar%20Light%20Pro-green.svg)

Esta integración personalizada permite controlar las pantallas LED **Twinstar Light Pro (RGBW)** directamente desde Home Assistant mediante Bluetooth (BLE). Está diseñada para ofrecer un control granular y una estabilidad industrial mediante reintentos automáticos.

## ✨ Características

* **Autodescubrimiento Bluetooth:** La integración detecta automáticamente nuevas lámparas Twinstar Light Pro en el área.
* **Soporte Multi-dispositivo:** Configura y controla múltiples acuarios de forma independiente.
* **Control de Canales Individuales:** Entidades `number` para ajustar Rojo, Verde, Azul, Blanco y Brillo General (0-100%).
* **Persistencia de Estado:** Los valores de los canales se restauran automáticamente tras reiniciar Home Assistant.
* **Servicios Avanzados:**
    * `send_command`: Envío de comandos crudos.
    * `send_sequence`: Ráfagas de comandos con retardos (ideal para efectos).
    * `encendido_silencioso`: Método especial para amaneceres que evita el "fogonazo" inicial.
* **Conexión Blindada:** Implementación de `bleak-retry-connector` para evitar desconexiones y errores de emparejamiento.

---

## 🛠️ Instalación

### Método Manual
1. Descarga el contenido de la carpeta `twinstar`.
2. Cópialo en tu directorio de Home Assistant: `/config/custom_components/twinstar/`.
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

## 💡 Servicios (Actions)

### `twinstar.send_command`
Envía un comando único (ej: `A50` para brillo al 50%).
* `entity_id`: La lámpara destino.
* `command`: El comando de texto.

### `twinstar.silent_on`
Ideal para automatizaciones de amanecer. Enciende la lámpara inyectando los colores actuales pero forzando el brillo al 1% para iniciar una rampa suave.

---

## 🌅 Ejemplo de Amanecer Pro (Script)

Este script realiza una rampa de 30 minutos sin bloquear el sistema y de forma segura para el controlador Bluetooth.

```yaml
alias: "Acuario: Amanecer"
sequence:
  - action: twinstar.silent_on
    target:
      entity_id: light.acuario_twinstar
  - delay: "00:00:02"
  - repeat:
      count: "{{ states('number.twinstar_brillo_general') | int }}"
      sequence:
        - action: twinstar.send_command
          data:
            command: "A{{ repeat.index }}"
            entity_id: light.acuario_twinstar
        - delay:
            seconds: "{{ (1800 / (states('number.twinstar_brillo_general') | int)) | round(1) }}"
```

---

## ⚠️ Disclaimer
Esta integración no es oficial de Twinstar. Ha sido desarrollada mediante ingeniería inversa para la comunidad de acuarofilia. Úsala bajo tu propia responsabilidad.

---
**Desarrollado con ❤️ para los amantes de los acuarios plantados.**
