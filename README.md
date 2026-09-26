# Noctune

Es una pequeña herramienta hecha para la terminal aun en mejora :D

cuenta con:

- Letras sincronizadas
- cuanta con dos visualizadores de audio en tiempo real basados en cava:
    
    - cava normal
    - cava circular

- Control de música mediante playerctl
- Experiencia completamente en terminal

---

## Vista previa
### imagenes de caso
![Caso1_letra encontrada](assets/caso1.png)
![Caso2_letra no encontrada](assets/caso2.png)

### video de uso
![Caso de uso](assets/noctune.gif)
---

## Características

- Letras sincronizadas en tiempo real
- Animación progresiva de letras
- Visualizador de audio con cava
- Configuracion visual compartia entre ambos visualizadores respetanto las configuraciones de cava
- Interfaz completamente en terminal 

---

## Controles

Los controles multimedia todavía no están integrados en el funcionamiento actual de Noctune.

La integración de `playerctl` y los controles mediante teclado se encuentra contemplada como una característica futura.

### Controles a integral

| Tecla   | Acción            |
| ------- | ----------------- |
| Alt + P | Play / Pause      |
| Alt + N | Siguiente canción |
| Alt + B | Canción anterior  |

### Controles ya integrados

| Tecla   | Acción            |
| ------- | ----------------- |
| Ctrl + c | salir de noctune      |

---

## Visualizadores

Noctune cuenta actualmente con dos modos de visualización.

### Visualizador de barras

Es el modo predeterminado:

noctune

Este visualizador utiliza un backend de Cava integrado en Noctune para obtener los datos del espectro de audio.

### Visualizador circular

El visualizador circular puede ejecutarse utilizando:

noctune -c

También puede utilizarse:

noctune --circle

El visualizador circular utiliza los mismos datos del backend de Cava y comparte su configuración visual.

---

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/Kevin-LemusOrt/Noctune
```

Ingresa al repositorio

```bash
cd Noctune
```

Dale permisos al instalador
```bash
chmod +x install.sh
```

Ejecuta el instalador

```bash
./install.sh
```

El instalador detecta automaticamente la ubicacion del proyecto a partir de `install.sh`.

Genera el launcher en
`~/.local/bin/noctune` y añade esa ruta al `PATH` de la configuracion de la
shell seleccionada.

Actualmente se detectan automáticamente los siguientes gestores de paquetes:

 - APT
 - DNF
 - Pacman

 El instalador prepara el entorno virtual de Python, instala las dependencias necesarias y genera el comando global:

```bash
 ~/.local/bin/noctune
```

También intenta configurar automáticamente el PATH dependiendo de la shell utilizada.

Las shells compatibles actualmente son:

 - fish
 - bash
 - zsh
 - sh
 - dash
 - ksh
 - mksh
 - csh
 - tcsh

 Una vez terminada la instalación, reinicia la terminal o recarga la configuración de la shell indicada por el instalador.

Después ejecuta:
```bash
noctune
```

O en su defecto si quiere usar el visaulizador circular

```bash
noctune -c

noctune --circle
```


# Troubleshooting

Si los archivos del sistema se crean pero quedan vacíos o incompletos, vuelva a ejecutar el instalador

```bash
./install.sh
```

El instalador comprueba que las dependencias principales estén disponibles y vuelve a preparar los archivos necesarios.

Esto puede ocurrir en casos como:

- Interrupción del proceso de instalación
- Problemas de permisos
- Ejecución parcial del script
- Fallos al crear el entorno virtual
- Fallos al escribir el launcher
- Problemas al configurar el `PATH`

En caso de que no se auto reparen al volver a ejecutar el `install.sh` puede arreglarlo manualmente:

### Comando noctune no funcional

En caso de que el comando `noctune` o `noctune -c` no funcione.

Verifica que el archivo del launcher exista:

```bash
ls ~/.local/bin/noctune
```
Si existe, comprueba si `~/.local/bin` está incluido en el `PATH`:

```bash
echo $PATH
```

Si no aparece, puedes agregarlo manualmente.

### Fish

Edite:

```bash
nano ~/.config/fish/config.fish
```

Y agrega:

```bash
fish_add_path ~/.local/bin
```

Despues recargue la configuracion de la shell:

```bash
source ~/.config/fish/config.fish
```

### Bash

Edite:

```bash
nano ~/.bashrc
```

Y agrega:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Despues recargue la configuracion de la shell:

```bash
source ~/.bashrc
```

### ZSH

Edite:

```bash
nano ~/.zshrc
```

Y agrega:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Despues recargue la configuracion de la shell:

```bash
source ~/.zshrc
```

Para otras shells, agrega ~/.local/bin al PATH utilizando el archivo de configuración correspondiente.

---

## El launcher de Noctune está vacío o no funciona

comprueba el contendio del launcher

```bash
cat ~/.local/bin/noctune
```

También puedes comprobar que tenga permisos de ejecución:

```bash
ls -l ~/.local/bin/noctune
```

Si el launcher está vacío, fue modificado o apunta a una ubicación incorrecta, vuelve a ejecutar:

```bash
./install.sh
```

El instalador volverá a generar el launcher utilizando la ubicación actual del proyecto.

### Reparación manual del launcher

Si el launcher está vacío, fue modificado o apunta a una ubicación incorrecta, puedes generarlo manualmente.

Primero entra al directorio principal de Noctune, donde se encuentra main.py:

```bash
cd Noctune
```

Comprueba que estás en la ubicación correcta:

```bash
pwd
```

Después guarda la ubicación actual del proyecto:

```bash
PROJECT_DIR="$(pwd)"
```

Crea el directorio del launcher si no existe:

```bash
mkdir -p "$HOME/.local/bin"
```

Genera nuevamente el launcher:

```bash
cat > "$HOME/.local/bin/noctune" <<EOF 
#!/bin/bash

exec "$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py" "\$@" 
EOF
```

Dale permisos de ejecución:

```bash
chmod +x "$HOME/.local/bin/noctune"
```

Comprueba que el launcher se haya creado correctamente:

```bash
cat "$HOME/.local/bin/noctune"
```

Finalmente, prueba Noctune:

```bash
noctune
```

O utiliza el visualizador circular:

```bash
noctune -c
```

También puedes utilizar:

```bash
noctune --circle
```

Este método utiliza automáticamente la ubicación actual del proyecto, por lo que no es necesario escribir manualmente la ruta del usuario ni modificar el launcher con una ruta específica.

## Requisitos

* Linux
* cava
* playerctl
* Python 3

El instalador se encarga automáticamente de instalar todo lo necesario.

---

## Dependencias de Python

* requests
* rich

Estas dependencias se instalan automáticamente dentro del entorno virtual de Noctune mediante requirements.txt.

---

## Ideas futuras

* múltiples fuentes de letras
* mejor sincronización
* Integración de controles multimedia mediante playerctl
* Mejoras en los visualizadores

## Hecho con

* Python
* cava
* playerctl
