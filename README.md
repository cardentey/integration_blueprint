# Twinstar Aquarium Light for Home Assistant

![Home Assistant Dashboard](https://img.shields.io/badge/Home%20Assistant-Integration-blue.svg)
![Bluetooth](https://img.shields.io/badge/Connectivity-BLE%20(USB%20or%20Proxy)-informational.svg)
![Model](https://img.shields.io/badge/Model-Twinstar%20Light%20Pro-green.svg)

Esta integración personalizada permite controlar las pantallas LED **Twinstar Light Pro (RGBW)** directamente desde Home Assistant utilizando **Bluetooth Low Energy (BLE)**.

La comunicación funciona con cualquier interfaz Bluetooth compatible con Home Assistant, incluyendo:

- ✅ Adaptador Bluetooth USB.
- ✅ Bluetooth integrado en el equipo donde se ejecuta Home Assistant (Raspberry Pi, NUC, etc.).
- ✅ ESPHome Bluetooth Proxy (recomendado para mejorar el alcance y la estabilidad de la conexión).

---

# 📦 Compatibilidad

## Probada con

- Twinstar V 600S

Es posible que también sea compatible con otros modelos **Twinstar Light Pro**, aunque no han sido verificados.

---

# 📋 Requerimientos

- Home Assistant.
- Bluetooth disponible en Home Assistant mediante cualquiera de estas opciones:
  - Adaptador Bluetooth USB.
  - Bluetooth integrado.
  - ESPHome Bluetooth Proxy (recomendado).

---

# ✨ Características

<p align="center">
  <img src="/IMG_7726.PNG" alt="Twinstar Dashboard" width="400">
</p>

- **Autodescubrimiento Bluetooth:** Detecta automáticamente nuevas lámparas Twinstar Light Pro cercanas.
- **Soporte Multi-dispositivo:** Control independiente de múltiples acuarios.
- **Control de Canales Individuales:** Entidades `number` para ajustar Rojo, Verde, Azul, Blanco y Brillo General (0–100%).
- **Temporizador en Hardware:** Configuración del amanecer, atardecer y horarios directamente en la memoria del controlador (`TOn:HHMM_HHMM_MM_MM`).
- **Sincronización del reloj:** Ajuste automático del RTC del controlador (`YYYYMMDDHHMMSS`) y botón manual `button.twinstar_sincronizar_reloj`.
- **Persistencia del estado:** Restauración automática de todos los valores tras reiniciar Home Assistant.
- **Servicios avanzados:**
  - `set_schedule`
  - `send_command`
  - `send_sequence`
- **Conexión robusta:** Utiliza `bleak-retry-connector` para minimizar desconexiones y mejorar la estabilidad de la comunicación Bluetooth.

---

# 🛠️ Instalación

## Instalación manual

1. Descarga el contenido de la carpeta:

```
custom_components/twinstar
```

2. Copia la carpeta en:

```
/config/custom_components/twinstar
```

3. Reinicia Home Assistant.

---

# ⚙️ Configuración

## Autodescubrimiento

La integración utiliza la infraestructura Bluetooth de Home Assistant.

Si Home Assistant puede comunicarse con la lámpara mediante cualquiera de estos métodos:

- Adaptador Bluetooth USB
- Bluetooth integrado
- ESPHome Bluetooth Proxy

aparecerá automáticamente una notificación de **"Nuevo dispositivo descubierto"**.

### Arquitectura de conexión

```text
                 Home Assistant
                        │
         ┌──────────────┴──────────────┐
         │                             │
 Bluetooth USB                  ESPHome Bluetooth Proxy
         │                             │
         └──────────────┬──────────────┘
                        │
                 Bluetooth LE (BLE)
                        │
              Twinstar Light Pro
```

---

## Configuración manual

Si el dispositivo no aparece automáticamente:

1. Ve a **Ajustes → Dispositivos y Servicios**.
2. Pulsa **Añadir integración**.
3. Busca **Twinstar**.
4. Introduce la dirección MAC de la lámpara.

---

# ⏱️ Programación nativa en el controlador

La integración configura directamente el temporizador interno y el reloj (RTC) del controlador Twinstar, evitando depender de automatizaciones externas.

### Funciones disponibles

- **Hora de encendido y apagado (`time`)**
  - Entidades de tipo `time` para configurar el horario diario.

- **Duración del amanecer y atardecer (`number`)**
  - Ajuste entre **0 y 60 minutos** para realizar transiciones suaves.

- **Resiliencia ante cortes eléctricos**
  - La integración monitoriza continuamente la conexión BLE.
  - Tras un reinicio de Home Assistant o un corte de alimentación superior a 60 segundos:
    - Resincroniza el reloj RTC.
    - Restaura automáticamente la programación.
    - Recupera los niveles RGBW y el brillo almacenados.
    - Mantiene la pantalla apagada si corresponde al horario nocturno.

- **Sincronización inteligente del estado**
  - Al iniciar Home Assistant, después de una recuperación y cada 5 minutos, se envía el comando:

```
powerstatus
```

- El controlador responde mediante:

```
WRITE_UUID: 0xdead
READ_UUID:  0xfef4
```

De este modo, si el temporizador interno enciende o apaga la pantalla, Home Assistant refleja siempre el estado real del dispositivo.

---

# 💡 Servicios (Actions)

## `twinstar.set_schedule`

Programa el horario directamente en el controlador.

### Parámetros

| Parámetro | Descripción |
|-----------|-------------|
| `entity_id` | Lámpara destino |
| `start_time` | Hora de encendido (ej. `09:00`) |
| `end_time` | Hora de apagado (ej. `21:00`) |
| `sunrise_minutes` | Duración del amanecer (0–60) |
| `sunset_minutes` | Duración del atardecer (0–60) |

---

## `twinstar.send_command`

Envía un comando de texto directamente al controlador.

### Parámetros

| Parámetro | Descripción |
|-----------|-------------|
| `entity_id` | Lámpara destino |
| `command` | Comando de texto (ej. `A50`) |

---

## `twinstar.send_sequence`

Envía una secuencia de comandos con retardos configurables.

Ideal para:

- Animaciones.
- Efectos personalizados.
- Automatizaciones avanzadas.

---

# ⚠️ Aviso

Esta integración **no es un producto oficial de Twinstar**.

Ha sido desarrollada mediante ingeniería inversa con fines de interoperabilidad para la comunidad de acuariofilia.

Utilízala bajo tu propia responsabilidad.

---

# ❤️ Agradecimientos

Desarrollado para la comunidad de Home Assistant y los amantes de los acuarios plantados.
