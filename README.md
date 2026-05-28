# Noctune

Es una paqueña herramienta hecha para la terminal aun en mejora :D
cuenta con:

* letras sincronizadas
* visualización de audio en tiempo real usando cava
* integración con tmux
* soporte para Spotify mediante playerctl
* Uso de cava (aun no de forma "nativa")

---

## Vista previa

```bash id="p4h0ea"
Now Playing: Ases Falsos - Simetría

────────────────────────────────────

          yo también pretendo
          mejorar el mundo...
```

---

## Características

* Letras sincronizadas en tiempo real
* Animación progresiva de letras
* Visualizador integrado con cava
* ⌨Controles multimedia
* Experiencia completamente en terminal

---

## Controles

| Tecla   | Acción            |
| ------- | ----------------- |
| Alt + P | Play / Pause      |
| Alt + N | Siguiente canción |
| Alt + B | Canción anterior  |
| Alt + Q | Salir de Noctune  |

---

## Instalación

Clona el repositorio:

```bash id="c23vlv"
git clone TU_REPO
cd noctune
```

Ejecuta el instalador:

```bash id="0v8lm2"
chmod +x install.sh
./install.sh
```

Después reinicia tu terminal o ejecuta:

```bash id="x2y8cf"
source ~/.bashrc
```

o:

```bash id="fwmv2r"
source ~/.zshrc
```

Finalmente inicia Noctune con:

```bash id="whn5sm"
noctune
```

---

## Requisitos

* Linux
* tmux
* cava
* playerctl
* Python 3

El instalador se encarga automáticamente de instalar todo lo necesario.

---

## Dependencias de Python

* requests
* rich

---

## Ideas futuras

* múltiples fuentes de letras
* mejor sincronización
* archivos de configuración
---

## Hecho con

* Python
* tmux
* cava
* playerctl
