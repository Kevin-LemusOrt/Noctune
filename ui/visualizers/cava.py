from pathlib import Path
import time

from ui.audio.cava_config import CavaConfig


BAR_LEVELS = " ▁▂▃▄▅▆▇█"
ANSI_RESET = "\033[0m"

CONFIG_CHECK_INTERVAL = 0.5


class CavaVisualizer:
    def __init__(self):
        self.previous_bars = []

        self.config = (
            CavaConfig()
            .load()
        )

        # ---------------------------------------------------------
        # CONFIGURACIÓN DE CAVA
        # ---------------------------------------------------------

        self._apply_config()

        # ---------------------------------------------------------
        # CONTROL DE RECARGA
        # ---------------------------------------------------------

        self._config_signature = (
            self._get_config_signature()
        )

        self._last_config_check = (
            time.monotonic()
        )

    # =============================================================
    # APLICAR CONFIGURACIÓN
    # =============================================================

    def _apply_config(self):
        """
        Aplica las opciones relevantes de la configuración
        actual de Cava.
        """

        self.bar_width = self.config.get_int(
            "general",
            "bar_width",
            1
        )

        self.bar_spacing = self.config.get_int(
            "general",
            "bar_spacing",
            0
        )

        self.center_align = self.config.get_bool(
            "general",
            "center_align",
            False
        )

        self.max_height = self.config.get_int(
            "general",
            "max_height",
            100
        )

        # Valores seguros
        self.bar_width = max(
            1,
            self.bar_width
        )

        self.bar_spacing = max(
            0,
            self.bar_spacing
        )

        self.max_height = max(
            1,
            min(
                100,
                self.max_height
            )
        )

    # =============================================================
    # RENDER
    # =============================================================

    def render(
        self,
        bars,
        width,
        height
    ):
        """
        Renderiza las barras utilizando la configuración
        activa de Cava.
        """

        if width <= 0 or height <= 0:
            return []

        if not bars:
            return [
                " " * width
                for _ in range(height)
            ]

        # ---------------------------------------------------------
        # AJUSTAR BARRAS AL ANCHO
        # ---------------------------------------------------------

        bars = _fit_bars_to_width(
            bars,
            width,
            self.bar_width,
            self.bar_spacing
        )

        # ---------------------------------------------------------
        # SUAVIZADO
        # ---------------------------------------------------------

        bars = self._smooth_bars(
            bars
        )

        # ---------------------------------------------------------
        # DIBUJAR
        # ---------------------------------------------------------

        return _draw_bars(
            bars,
            width,
            height,
            self.bar_width,
            self.bar_spacing,
            self.center_align,
            self.max_height
        )

    # =============================================================
    # COLOR
    # =============================================================

    def colorize(
        self,
        lines,
        width
    ):
        """
        Aplica los colores del tema actual de Cava.

        Si el tema utiliza gradiente, se aplica de acuerdo
        con la altura de cada barra.

        La configuración se comprueba periódicamente para
        permitir cambios dinámicos sin añadir trabajo
        innecesario a cada frame.
        """

        self._reload_config_if_changed()

        colors = self.config.get_colors()

        if not colors:
            return lines

        # ---------------------------------------------------------
        # CONFIGURACIÓN DE COLOR
        # ---------------------------------------------------------

        foreground = colors.get(
            "foreground"
        )

        if not foreground:
            foreground = colors.get(
                "color"
            )

        gradient_enabled = _parse_bool(
            colors.get(
                "gradient",
                "0"
            )
        )

        horizontal_gradient = _parse_bool(
            colors.get(
                "horizontal_gradient",
                "0"
            )
        )

        gradient_colors = _get_gradient_colors(
            colors,
            foreground
        )

        # ---------------------------------------------------------
        # SIN COLOR
        # ---------------------------------------------------------

        if (
            not foreground
            and not gradient_colors
        ):
            return lines

        # ---------------------------------------------------------
        # RENDERIZAR COLOR
        # ---------------------------------------------------------

        colored_lines = []

        total_height = max(
            1,
            len(lines)
        )

        for row_index, line in enumerate(
            lines
        ):

            result = []

            visible_line = line[
                :width
            ]

            for column_index, character in enumerate(
                visible_line
            ):

                if character == " ":

                    result.append(
                        character
                    )

                    continue

                # -------------------------------------------------
                # DETERMINAR COLOR
                # -------------------------------------------------

                if (
                    gradient_enabled
                    and gradient_colors
                ):

                    if horizontal_gradient:

                        position = _normalized_position(
                            column_index,
                            max(
                                1,
                                len(visible_line) - 1
                            )
                        )

                    else:

                        # Las barras crecen desde abajo.
                        # Abajo = color inicial.
                        # Arriba = color final.
                        position = _normalized_position(
                            total_height - 1 - row_index,
                            max(
                                1,
                                total_height - 1
                            )
                        )

                    color = _interpolate_gradient(
                        gradient_colors,
                        position
                    )

                else:

                    color = foreground

                ansi_color = _ansi_fg(
                    color
                )

                if not ansi_color:

                    result.append(
                        character
                    )

                    continue

                result.extend([
                    ansi_color,
                    character,
                    ANSI_RESET
                ])

            visible_length = len(
                visible_line
            )

            if visible_length < width:

                result.append(
                    " "
                    * (
                        width
                        - visible_length
                    )
                )

            colored_lines.append(
                "".join(result)
            )

        return colored_lines

    # =============================================================
    # RECARGA DE CONFIGURACIÓN
    # =============================================================

    def _reload_config_if_changed(self):
        """
        Comprueba periódicamente si cambió la configuración
        de Cava o su tema.

        No realiza comprobaciones del sistema de archivos
        en cada frame.
        """

        now = time.monotonic()

        if (
            now
            - self._last_config_check
            < CONFIG_CHECK_INTERVAL
        ):
            return

        self._last_config_check = now

        signature = (
            self._get_config_signature()
        )

        if signature == self._config_signature:
            return

        new_config = (
            CavaConfig()
            .load()
        )

        self.config = new_config

        self._apply_config()

        self._config_signature = (
            self._get_config_signature()
        )

    def _get_config_signature(self):
        """
        Obtiene una firma basada en las fechas de modificación
        de la configuración principal y del tema activo.
        """

        config_path = (
            self.config.config_path
        )

        config_mtime = _get_mtime(
            config_path
        )

        theme_path = (
            self.config.theme_path
        )

        theme_mtime = _get_mtime(
            theme_path
        )

        return (
            str(config_path),
            config_mtime,
            str(theme_path)
            if theme_path
            else None,
            theme_mtime
        )

    # =============================================================
    # SUAVIZADO
    # =============================================================

    def _smooth_bars(
        self,
        bars
    ):
        """
        Suaviza los cambios entre frames.

        Las barras suben rápidamente y bajan
        progresivamente.

        Cuando Cava entrega cero, el valor anterior
        se mantiene parcialmente y va decayendo
        gradualmente.
        """

        if (
            not self.previous_bars
            or len(self.previous_bars) != len(bars)
        ):

            self.previous_bars = bars.copy()

            return bars

        smoothed = []

        for current, previous in zip(
            bars,
            self.previous_bars
        ):

            # -----------------------------------------------------
            # SUBIDA
            # -----------------------------------------------------

            if current > previous:

                value = (
                    previous * 0.25
                    + current * 0.75
                )

            # -----------------------------------------------------
            # BAJADA
            # -----------------------------------------------------

            else:

                if current <= 0.0:

                    value = (
                        previous * 0.90
                    )

                else:

                    value = (
                        previous * 0.80
                        + current * 0.20
                    )

            smoothed.append(
                max(
                    0.0,
                    min(
                        1.0,
                        value
                    )
                )
            )

        self.previous_bars = smoothed

        return smoothed


# =============================================================
# PUNTOS DE ENTRADA
# =============================================================

def render(
    bars,
    width,
    height
):
    """
    Punto de entrada utilizado por renderer.py.
    """

    if not hasattr(
        render,
        "_visualizer"
    ):

        render._visualizer = (
            CavaVisualizer()
        )

    return render._visualizer.render(
        bars,
        width,
        height
    )


def colorize(
    lines,
    width
):
    """
    Colorea líneas ya ajustadas,
    conservando su contenido visible.
    """

    if not hasattr(
        render,
        "_visualizer"
    ):

        render._visualizer = (
            CavaVisualizer()
        )

    return render._visualizer.colorize(
        lines,
        width
    )


# =============================================================
# CONFIGURACIÓN / COLORES
# =============================================================

def _parse_bool(
    value
):
    """
    Convierte valores típicos de configuración
    de Cava a booleano.
    """

    if value is None:
        return False

    value = str(
        value
    ).strip().lower()

    return value in (
        "1",
        "true",
        "yes",
        "on"
    )


def _get_gradient_colors(
    colors,
    foreground
):
    """
    Obtiene los colores del gradiente de Cava.

    Se soportan:

        gradient_color_1
        gradient_color_2
        gradient_color_3
    """

    gradient = []

    for key in (
        "gradient_color_1",
        "gradient_color_2",
        "gradient_color_3"
    ):

        color = colors.get(
            key
        )

        if color:

            color = _normalize_color(
                color
            )

            if color:

                gradient.append(
                    color
                )

    if gradient:
        return gradient

    if foreground:

        foreground = _normalize_color(
            foreground
        )

        if foreground:

            return [
                foreground
            ]

    return []


def _normalize_color(
    color
):
    """
    Normaliza un color hexadecimal.
    """

    if color is None:
        return None

    color = str(
        color
    ).strip()

    if color.startswith("#"):
        color = color[1:]

    if len(color) != 6:
        return None

    try:

        int(
            color,
            16
        )

    except ValueError:

        return None

    return (
        "#"
        + color.lower()
    )


def _interpolate_gradient(
    colors,
    position
):
    """
    Interpola entre los colores del gradiente.

    Con tres colores:

        0.0 -> color 1
        0.5 -> color 2
        1.0 -> color 3

    Con dos colores:

        0.0 -> color 1
        1.0 -> color 2
    """

    if not colors:
        return None

    if len(colors) == 1:
        return colors[0]

    position = max(
        0.0,
        min(
            1.0,
            position
        )
    )

    segments = (
        len(colors) - 1
    )

    scaled = (
        position
        * segments
    )

    index = int(
        scaled
    )

    if index >= segments:
        return colors[-1]

    fraction = (
        scaled
        - index
    )

    first = _hex_to_rgb(
        colors[index]
    )

    second = _hex_to_rgb(
        colors[index + 1]
    )

    if (
        first is None
        or second is None
    ):

        return colors[index]

    red = round(
        first[0]
        + (
            second[0]
            - first[0]
        )
        * fraction
    )

    green = round(
        first[1]
        + (
            second[1]
            - first[1]
        )
        * fraction
    )

    blue = round(
        first[2]
        + (
            second[2]
            - first[2]
        )
        * fraction
    )

    return (
        f"#{red:02x}"
        f"{green:02x}"
        f"{blue:02x}"
    )


def _hex_to_rgb(
    color
):
    """
    Convierte #RRGGBB a una tupla RGB.
    """

    color = _normalize_color(
        color
    )

    if color is None:
        return None

    value = color[1:]

    return (
        int(
            value[0:2],
            16
        ),
        int(
            value[2:4],
            16
        ),
        int(
            value[4:6],
            16
        )
    )


def _normalized_position(
    value,
    maximum
):
    """
    Normaliza un valor entre 0.0 y 1.0.
    """

    if maximum <= 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            value / maximum
        )
    )


def _ansi_fg(
    color
):
    """
    Convierte #RRGGBB a ANSI truecolor.
    """

    color = _normalize_color(
        color
    )

    if color is None:
        return ""

    value = color[1:]

    red = int(
        value[0:2],
        16
    )

    green = int(
        value[2:4],
        16
    )

    blue = int(
        value[4:6],
        16
    )

    return (
        f"\033[38;2;"
        f"{red};{green};{blue}m"
    )


def _get_mtime(
    path
):
    """
    Obtiene la fecha de modificación de un archivo.

    Devuelve None si el archivo no existe.
    """

    if path is None:
        return None

    try:

        return Path(
            path
        ).stat().st_mtime_ns

    except OSError:

        return None


# =============================================================
# BARRAS
# =============================================================

def _fit_bars_to_width(
    bars,
    width,
    bar_width=1,
    bar_spacing=0
):
    """
    Ajusta la cantidad de barras al ancho disponible.

    Respeta bar_width y bar_spacing de Cava.

    Si hay demasiadas barras:
        se reducen mediante downsampling.

    Si hay pocas:
        se interpolan para aprovechar
        todo el espacio horizontal disponible.
    """

    if width <= 0:
        return []

    if not bars:
        return []

    bar_width = max(
        1,
        bar_width
    )

    bar_spacing = max(
        0,
        bar_spacing
    )

    cell_width = (
        bar_width
        + bar_spacing
    )

    max_bars = (
        width
        + bar_spacing
    ) // cell_width

    max_bars = max(
        1,
        max_bars
    )

    if len(bars) > max_bars:

        return _downsample(
            bars,
            max_bars
        )

    target_size = max_bars

    if len(bars) == target_size:
        return bars

    if len(bars) == 1:
        return bars * target_size

    result = []

    source_size = len(bars)

    for index in range(
        target_size
    ):

        position = (
            index
            * (source_size - 1)
            / (target_size - 1)
        )

        left = int(
            position
        )

        right = min(
            left + 1,
            source_size - 1
        )

        fraction = (
            position
            - left
        )

        value = (
            bars[left]
            * (1 - fraction)
            + bars[right]
            * fraction
        )

        result.append(
            value
        )

    return result


def _downsample(
    values,
    target_size
):
    """
    Reduce la cantidad de barras conservando
    los picos de cada grupo.
    """

    if target_size <= 0:
        return []

    if len(values) <= target_size:
        return values.copy()

    result = []

    source_size = len(values)

    for index in range(
        target_size
    ):

        start = int(
            index
            * source_size
            / target_size
        )

        end = int(
            (index + 1)
            * source_size
            / target_size
        )

        if end <= start:
            end = start + 1

        chunk = values[
            start:end
        ]

        if chunk:

            result.append(
                max(chunk)
            )

        else:

            result.append(
                0.0
            )

    return result


def _normalize_bars(
    bars
):
    """
    Normaliza las barras entre 0.0 y 1.0.

    Se conserva por compatibilidad con el código,
    pero NO se utiliza durante el renderizado.

    Cava ya entrega valores normalizados.
    """

    if not bars:
        return bars

    maximum = max(
        bars
    )

    if maximum <= 0:
        return bars

    return [
        max(
            0.0,
            min(
                1.0,
                value / maximum
            )
        )
        for value in bars
    ]


# =============================================================
# DIBUJADO
# =============================================================

def _draw_bars(
    bars,
    width,
    height,
    bar_width=1,
    bar_spacing=0,
    center_align=False,
    max_height=100
):
    """
    Dibuja las barras respetando:

        bar_width
        bar_spacing
        center_align
        max_height
    """

    if width <= 0 or height <= 0:
        return []

    if not bars:
        return [
            " " * width
            for _ in range(height)
        ]

    bar_width = max(
        1,
        bar_width
    )

    bar_spacing = max(
        0,
        bar_spacing
    )

    # ---------------------------------------------------------
    # LIMITAR ALTURA
    # ---------------------------------------------------------

    usable_height = min(
        height,
        max(
            1,
            int(
                height
                * max_height
                / 100
            )
        )
    )

    # ---------------------------------------------------------
    # ESPACIO TOTAL
    # ---------------------------------------------------------

    total_width = (
        len(bars)
        * bar_width
        + max(
            0,
            len(bars) - 1
        )
        * bar_spacing
    )

    # ---------------------------------------------------------
    # POSICIÓN HORIZONTAL
    # ---------------------------------------------------------

    if center_align:

        offset = max(
            0,
            (
                width
                - total_width
            ) // 2
        )

    else:

        offset = 0

    # ---------------------------------------------------------
    # LIENZO
    # ---------------------------------------------------------

    lines = [
        [" "] * width
        for _ in range(height)
    ]

    # ---------------------------------------------------------
    # DIBUJAR BARRAS
    # ---------------------------------------------------------

    for index, value in enumerate(
        bars
    ):

        value = max(
            0.0,
            min(
                1.0,
                value
            )
        )

        exact_height = (
            value
            * usable_height
        )

        full_rows = int(
            exact_height
        )

        remainder = (
            exact_height
            - full_rows
        )

        x = (
            offset
            + index
            * (
                bar_width
                + bar_spacing
            )
        )

        # -----------------------------------------------------
        # BARRA COMPLETA
        # -----------------------------------------------------

        for offset_y in range(
            full_rows
        ):

            y = (
                height
                - 1
                - offset_y
            )

            if y < 0:
                break

            for bar_x in range(
                bar_width
            ):

                current_x = (
                    x
                    + bar_x
                )

                if (
                    0
                    <= current_x
                    < width
                ):

                    lines[y][
                        current_x
                    ] = "█"

        # -----------------------------------------------------
        # PARTE FRACCIONAL
        # -----------------------------------------------------

        if (
            full_rows < usable_height
            and remainder > 0
        ):

            level = int(
                remainder
                * (
                    len(BAR_LEVELS)
                    - 1
                )
            )

            y = (
                height
                - 1
                - full_rows
            )

            if y >= 0:

                character = (
                    BAR_LEVELS[
                        level
                    ]
                )

                for bar_x in range(
                    bar_width
                ):

                    current_x = (
                        x
                        + bar_x
                    )

                    if (
                        0
                        <= current_x
                        < width
                    ):

                        lines[y][
                            current_x
                        ] = character

    return [
        "".join(line)
        for line in lines
    ]