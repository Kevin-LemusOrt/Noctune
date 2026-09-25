import math
import time
from pathlib import Path

from ui.audio.cava_config import CavaConfig


ANSI_RESET = "\033[0m"

CONFIG_CHECK_INTERVAL = 0.5


class CircularVisualizer:
    """
    Visualizador de espectro circular.

    Utiliza la misma configuración de Cava que CavaVisualizer.

    Configuración compartida:

        [general]
        bar_width
        bar_spacing
        max_height

        [color]
        foreground
        gradient
        gradient_color_1
        gradient_color_2
        gradient_color_3
        horizontal_gradient

    Si Cava utiliza un tema, CavaConfig carga automáticamente
    los colores de dicho tema.

    El círculo conserva su propia geometría radial, pero
    comparte el sistema de configuración y colores con Cava.
    """

    def __init__(
        self,
        min_radius=5.0,
        sensitivity=1.35,
        max_bar_length=14.0,
        angular_resolution=360,
    ):
        # ---------------------------------------------------------
        # GEOMETRÍA DEL CÍRCULO
        # ---------------------------------------------------------

        self.min_radius = max(
            0.0,
            float(min_radius)
        )

        self.sensitivity = max(
            0.0,
            float(sensitivity)
        )

        self.max_bar_length = max(
            1.0,
            float(max_bar_length)
        )

        self.angular_resolution = max(
            36,
            int(angular_resolution)
        )

        # ---------------------------------------------------------
        # CONFIGURACIÓN DE CAVA
        # ---------------------------------------------------------

        self.config = (
            CavaConfig()
            .load()
        )

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

        # ---------------------------------------------------------
        # SUAVIZADO
        # ---------------------------------------------------------

        self.previous_bars = []

    # =============================================================
    # CONFIGURACIÓN
    # =============================================================

    def _apply_config(self):
        """
        Aplica la configuración actual de Cava.

        Las opciones que tienen sentido para el visualizador
        circular se utilizan aquí.
        """

        # ---------------------------------------------------------
        # GENERAL
        # ---------------------------------------------------------

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

        self.max_height = self.config.get_int(
            "general",
            "max_height",
            100
        )

        # ---------------------------------------------------------
        # VALORES SEGUROS
        # ---------------------------------------------------------

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
        Renderiza el espectro circular.
        """

        if width <= 0 or height <= 0:
            return []

        # ---------------------------------------------------------
        # RECARGAR CONFIGURACIÓN SI CAMBIÓ
        # ---------------------------------------------------------

        self._reload_config_if_changed()

        if not bars:
            return [
                " " * width
                for _ in range(height)
            ]

        # ---------------------------------------------------------
        # SUAVIZADO
        # ---------------------------------------------------------

        bars = self._smooth_bars(
            bars
        )

        # ---------------------------------------------------------
        # DIBUJAR
        # ---------------------------------------------------------

        return self._draw_circle(
            bars,
            width,
            height
        )

    # =============================================================
    # RECARGA DE CONFIGURACIÓN
    # =============================================================

    def _reload_config_if_changed(self):
        """
        Comprueba periódicamente si cambió la configuración
        de Cava o el tema activo.
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

        self.config = (
            CavaConfig()
            .load()
        )

        self._apply_config()

        self._config_signature = (
            self._get_config_signature()
        )

    def _get_config_signature(self):
        """
        Obtiene una firma basada en los archivos de configuración
        de Cava y del tema activo.
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
        Utiliza el mismo suavizado que CavaVisualizer.

        Las barras suben rápidamente y bajan progresivamente.
        """

        current_bars = []

        for value in bars:

            try:
                value = float(value)

            except (TypeError, ValueError):
                value = 0.0

            current_bars.append(
                max(
                    0.0,
                    min(
                        1.0,
                        value
                    )
                )
            )

        if (
            not self.previous_bars
            or len(
                self.previous_bars
            ) != len(current_bars)
        ):

            self.previous_bars = (
                current_bars.copy()
            )

            return current_bars

        smoothed = []

        for current, previous in zip(
            current_bars,
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
    # COLOR
    # =============================================================

    def _get_color(
        self,
        progress
    ):
        """
        Obtiene el color según la configuración actual de Cava.

        El gradiente se aplica radialmente:

            0.0 -> centro
            1.0 -> punta de la barra
        """

        colors = self.config.get_colors()

        if not colors:
            return None

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

        gradient_colors = _get_gradient_colors(
            colors,
            foreground
        )

        # ---------------------------------------------------------
        # GRADIENTE
        # ---------------------------------------------------------

        if (
            gradient_enabled
            and gradient_colors
        ):
            return _interpolate_gradient(
                gradient_colors,
                progress
            )

        # ---------------------------------------------------------
        # COLOR ÚNICO
        # ---------------------------------------------------------

        return _normalize_color(
            foreground
        )

    # =============================================================
    # INTERPOLACIÓN ANGULAR
    # =============================================================

    def _interpolate_bars(
        self,
        bars
    ):
        """
        Distribuye las barras alrededor de 360 grados.
        """

        count = len(bars)

        if count == 0:
            return []

        if count == 1:
            return [
                bars[0]
            ] * self.angular_resolution

        result = []

        for position in range(
            self.angular_resolution
        ):

            location = (
                position
                * count
                / self.angular_resolution
            )

            index = int(
                math.floor(location)
            )

            fraction = (
                location
                - index
            )

            current = bars[
                index % count
            ]

            next_value = bars[
                (index + 1) % count
            ]

            value = (
                current
                + (
                    next_value
                    - current
                )
                * fraction
            )

            result.append(
                value
            )

        return result

    # =============================================================
    # CÍRCULO
    # =============================================================

    def _draw_circle(
        self,
        bars,
        width,
        height
    ):
        """
        Construye el canvas y dibuja las barras radiales.
        """

        canvas = [
            [" " for _ in range(width)]
            for _ in range(height)
        ]

        # ---------------------------------------------------------
        # CENTRO
        # ---------------------------------------------------------

        center_x = (
            width - 1
        ) / 2.0

        center_y = (
            height - 1
        ) / 2.0

        # ---------------------------------------------------------
        # RELACIÓN DE ASPECTO
        # ---------------------------------------------------------

        char_ratio = 2.0

        available_width = max(
            0.0,
            width - 4.0
        )

        available_height = max(
            0.0,
            height - 4.0
        )

        max_radius_x = (
            available_width / 2.0
        )

        max_radius_y = (
            available_height
            * char_ratio
            / 2.0
        )

        radius = min(
            max_radius_x,
            max_radius_y
        )

        if radius <= 0:
            return [
                "".join(row)
                for row in canvas
            ]

        # ---------------------------------------------------------
        # HUECO CENTRAL
        # ---------------------------------------------------------

        inner_radius = min(
            self.min_radius,
            radius - 2.0
        )

        inner_radius = max(
            0.0,
            inner_radius
        )

        inner_radius_x = (
            inner_radius
        )

        inner_radius_y = (
            inner_radius
            / char_ratio
        )

        # ---------------------------------------------------------
        # LONGITUD MÁXIMA
        # ---------------------------------------------------------

        available_length = min(
            self.max_bar_length,
            radius - inner_radius
        )

        if available_length <= 0:
            return [
                "".join(row)
                for row in canvas
            ]

        # ---------------------------------------------------------
        # BARRAS ANGULARES
        # ---------------------------------------------------------

        visual_bars = (
            self._interpolate_bars(
                bars
            )
        )

        count = len(
            visual_bars
        )

        if count == 0:
            return [
                "".join(row)
                for row in canvas
            ]

        angle_step = (
            math.tau
            / count
        )

        # ---------------------------------------------------------
        # DIBUJAR
        # ---------------------------------------------------------

        for index, value in enumerate(
            visual_bars
        ):

            # Aplicar max_height de Cava
            value *= (
                self.max_height
                / 100.0
            )

            value = max(
                0.0,
                min(
                    1.0,
                    value
                )
            )

            length = (
                value
                * available_length
            )

            if length < 0.10:
                continue

            angle = (
                -math.pi / 2.0
                + index * angle_step
            )

            self._draw_bar(
                canvas,
                center_x,
                center_y,
                inner_radius_x,
                inner_radius_y,
                length,
                angle,
                width,
                height
            )

        return [
            "".join(row)
            for row in canvas
        ]

    # =============================================================
    # BARRA RADIAL
    # =============================================================

    def _draw_bar(
        self,
        canvas,
        center_x,
        center_y,
        inner_radius_x,
        inner_radius_y,
        length,
        angle,
        width,
        height
    ):
        """
        Dibuja una barra radial.

        bar_width y bar_spacing de Cava se traducen a la
        separación angular del círculo.
        """

        steps = max(
            2,
            int(
                length
                * 8.0
            )
        )

        cos_angle = math.cos(
            angle
        )

        sin_angle = math.sin(
            angle
        )

        for step in range(
            steps + 1
        ):

            progress = (
                step
                / steps
            )

            radius_x = (
                inner_radius_x
                + length
                * progress
            )

            radius_y = (
                inner_radius_y
                + (
                    length
                    * progress
                    / 2.0
                )
            )

            x = (
                center_x
                + cos_angle
                * radius_x
            )

            y = (
                center_y
                + sin_angle
                * radius_y
            )

            color = self._get_color(
                progress
            )

            self._put_pixel(
                canvas,
                int(round(x)),
                int(round(y)),
                width,
                height,
                color
            )

    # =============================================================
    # PIXEL
    # =============================================================

    def _put_pixel(
        self,
        canvas,
        x,
        y,
        width,
        height,
        color
    ):
        """
        Coloca un carácter coloreado.
        """

        if x < 0 or x >= width:
            return

        if y < 0 or y >= height:
            return

        if not color:
            canvas[y][x] = "▪"
            return

        color = _normalize_color(
            color
        )

        if not color:
            canvas[y][x] = "▪"
            return

        rgb = _hex_to_rgb(
            color
        )

        if rgb is None:
            canvas[y][x] = "▪"
            return

        red, green, blue = rgb

        canvas[y][x] = (
            f"\033[38;2;"
            f"{red};{green};{blue}m"
            + "●"
            + ANSI_RESET
        )


# =============================================================
# COLOR
# =============================================================

def _parse_bool(
    value
):
    """
    Convierte valores típicos de configuración de Cava
    a booleano.
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

    Ejemplo:

        #afc9e6

    devuelve:

        #afc9e6
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


def _hex_to_rgb(
    color
):
    """
    Convierte #RRGGBB a RGB.
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
        len(colors)
        - 1
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


# =============================================================
# ARCHIVOS
# =============================================================

def _get_mtime(
    path
):
    """
    Obtiene la fecha de modificación de un archivo.
    """

    if path is None:
        return None

    try:

        return Path(
            path
        ).stat().st_mtime_ns

    except OSError:

        return None