import math
import time
from pathlib import Path

from ui.audio.cava_config import CavaConfig


ANSI_RESET = "\033[0m"

CONFIG_CHECK_INTERVAL = 0.5

CENTER_OFFSET_X = 4.0


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

    El círculo adapta automáticamente su tamaño a la terminal.
    La longitud de las barras también escala con el radio disponible.

    El círculo conserva su propia geometría radial, pero comparte
    el sistema de configuración y colores con Cava.
    """

    def __init__(
        self,
        min_radius=4.0,
        sensitivity=1.35,
        max_bar_length=100.0,
        angular_resolution=360,
    ):
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

        self.config = CavaConfig().load()

        self._apply_config()

        self._config_signature = (
            self._get_config_signature()
        )

        self._last_config_check = (
            time.monotonic()
        )

        self.previous_bars = []

    def _apply_config(self):
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
            min(100, self.max_height)
        )

    def render(self, bars, width, height):
        if width <= 0 or height <= 0:
            return []

        self._reload_config_if_changed()

        if not bars:
            return [
                " " * width
                for _ in range(height)
            ]

        bars = self._smooth_bars(bars)

        return self._draw_circle(
            bars,
            width,
            height
        )

    def _reload_config_if_changed(self):
        now = time.monotonic()

        if (
            now - self._last_config_check
            < CONFIG_CHECK_INTERVAL
        ):
            return

        self._last_config_check = now

        signature = self._get_config_signature()

        if signature == self._config_signature:
            return

        self.config = CavaConfig().load()

        self._apply_config()

        self._config_signature = (
            self._get_config_signature()
        )

    def _get_config_signature(self):
        config_path = self.config.config_path
        config_mtime = _get_mtime(config_path)

        theme_path = self.config.theme_path
        theme_mtime = _get_mtime(theme_path)

        return (
            str(config_path),
            config_mtime,
            str(theme_path) if theme_path else None,
            theme_mtime,
        )

    def _smooth_bars(self, bars):
        current_bars = []

        for value in bars:
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0.0

            current_bars.append(
                max(
                    0.0,
                    min(1.0, value)
                )
            )

        if (
            not self.previous_bars
            or len(self.previous_bars)
            != len(current_bars)
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
            if current > previous:
                value = (
                    previous * 0.25
                    + current * 0.75
                )

            else:
                if current <= 0.0:
                    value = previous * 0.90

                else:
                    value = (
                        previous * 0.80
                        + current * 0.20
                    )

            smoothed.append(
                max(
                    0.0,
                    min(1.0, value)
                )
            )

        self.previous_bars = smoothed

        return smoothed

    def _get_color(self, progress):
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
            colors.get("gradient", "0")
        )

        gradient_colors = (
            _get_gradient_colors(
                colors,
                foreground
            )
        )

        if (
            gradient_enabled
            and gradient_colors
        ):
            return _interpolate_gradient(
                gradient_colors,
                progress
            )

        return _normalize_color(
            foreground
        )

    def _prepare_colors(self):
        """
        Prepara la información de color una sola vez
        por frame.

        Antes _get_color() consultaba la configuración
        y reconstruía la información del gradiente
        para cada punto dibujado.
        """

        colors = self.config.get_colors()

        if not colors:
            return {
                "gradient": False,
                "foreground": None,
                "gradient_colors": [],
            }

        foreground = colors.get(
            "foreground"
        )

        if not foreground:
            foreground = colors.get(
                "color"
            )

        foreground = _normalize_color(
            foreground
        )

        gradient_enabled = _parse_bool(
            colors.get("gradient", "0")
        )

        gradient_colors = (
            _get_gradient_colors(
                colors,
                foreground
            )
        )

        return {
            "gradient": (
                gradient_enabled
                and len(gradient_colors) > 0
            ),
            "foreground": foreground,
            "gradient_colors": gradient_colors,
        }

    def _get_cached_color(
        self,
        progress,
        color_data
    ):
        """
        Obtiene el color usando la información
        preparada para el frame actual.
        """

        if not color_data:
            return None

        if color_data["gradient"]:
            return _interpolate_gradient(
                color_data["gradient_colors"],
                progress
            )

        return color_data["foreground"]

    def _get_angular_resolution(self, radius):
        """
        Ajusta la cantidad de puntos según
        el tamaño real del círculo.

        En círculos pequeños no tiene sentido
        calcular 360 posiciones si muchas terminarán
        dibujándose sobre las mismas celdas de terminal.

        En terminales grandes se limita la resolución
        para evitar cálculos innecesarios que pueden
        afectar la fluidez del visualizador.
        """

        resolution = int(
            radius * 10.0
        )

        return max(
            72,
            min(
                300,
                self.angular_resolution,
                resolution
            )
        )

    def _interpolate_bars(
        self,
        bars,
        resolution=None
    ):
        count = len(bars)

        if count == 0:
            return []

        if resolution is None:
            resolution = (
                self.angular_resolution
            )

        resolution = max(
            1,
            int(resolution)
        )

        if count == 1:
            return [
                bars[0]
            ] * resolution

        result = []

        for position in range(
            resolution
        ):
            location = (
                position
                * count
                / resolution
            )

            index = int(
                math.floor(location)
            )

            fraction = (
                location - index
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

            result.append(value)

        return result

    def _draw_circle(
        self,
        bars,
        width,
        height
    ):
        canvas = [
            [" " for _ in range(width)]
            for _ in range(height)
        ]

        center_y = (
            height - 1
        ) / 2.0

        # El desplazamiento se adapta al tamaño
        # de la terminal.
        #
        # En terminales pequeñas se reduce para
        # evitar que el círculo pierda demasiado
        # espacio horizontal.
        center_offset_x = min(
            CENTER_OFFSET_X,
            max(
                0.0,
                width * 0.05
            )
        )

        center_x = (
            (width - 1) / 2.0
            + center_offset_x
        )

        # La terminal no tiene píxeles cuadrados.
        # Un carácter suele ser aproximadamente el doble
        # de alto que de ancho.
        char_ratio = 2.0

        # En terminales pequeñas aprovechamos más
        # espacio para que el círculo conserve
        # presencia visual.
        if width < 70:
            available_width = max(
                0.0,
                width - 2.0
            )

            available_height = max(
                0.0,
                height - 2.0
            )

        else:
            available_width = max(
                0.0,
                width - 4.0
            )

            available_height = max(
                0.0,
                height - 4.0
            )

        # Calculamos cuánto espacio queda realmente
        # a cada lado del centro desplazado.
        max_radius_x = min(
            center_x - 2.0,
            width - center_x - 2.0
        )

        max_radius_x = max(
            0.0,
            max_radius_x
        )

        max_radius_y = (
            available_height
            * char_ratio
            / 2.0
        )

        # El radio se adapta automáticamente
        # al ancho y alto disponibles.
        radius = min(
            max_radius_x,
            max_radius_y
        )

        if radius <= 0:
            return [
                "".join(row)
                for row in canvas
            ]

        # El centro interior crece proporcionalmente
        # al tamaño del círculo.
        #
        # En terminales pequeñas aumentamos el centro
        # para que el círculo mantenga presencia visual.
        if width < 70:
            inner_radius = max(
                self.min_radius,
                radius * 0.40
            )

        else:
            inner_radius = max(
                self.min_radius,
                radius * 0.35
            )

        # Evitamos que el centro llegue a ocupar
        # todo el círculo en terminales pequeñas.
        inner_radius = min(
            inner_radius,
            radius * 0.45,
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

        # La longitud de las barras depende
        # directamente del radio disponible.
        #
        # En terminales pequeñas dejamos que recorran
        # casi todo el espacio disponible entre el centro
        # y el borde.
        if width < 70:
            available_length = min(
                self.max_bar_length,
                (
                    radius
                    - inner_radius
                ) * 0.98
            )

        else:
            available_length = min(
                self.max_bar_length,
                (
                    radius
                    - inner_radius
                ) * 0.90
            )

        if available_length <= 0:
            return [
                "".join(row)
                for row in canvas
            ]

        # La resolución angular se adapta al tamaño
        # pero tiene un límite para mantener la fluidez.
        angular_resolution = (
            self._get_angular_resolution(
                radius
            )
        )

        visual_bars = (
            self._interpolate_bars(
                bars,
                angular_resolution
            )
        )

        count = len(visual_bars)

        if count == 0:
            return [
                "".join(row)
                for row in canvas
            ]

        angle_step = (
            math.tau / count
        )

        # Preparamos los colores una sola vez
        # en lugar de reconstruirlos por cada punto.
        color_data = self._prepare_colors()

        for index, value in enumerate(
            visual_bars
        ):
            value *= (
                self.max_height
                / 100.0
            )

            # Aplicamos la sensibilidad propia
            # del visualizador.
            value *= self.sensitivity

            value = max(
                0.0,
                min(1.0, value)
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
                height,
                color_data
            )

        return [
            "".join(row)
            for row in canvas
        ]

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
        height,
        color_data
    ):
        steps = max(
            2,
            int(length * 4.0)
        )

        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        for step in range(
            steps + 1
        ):
            progress = (
                step / steps
            )

            radius_x = (
                inner_radius_x
                + length * progress
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
                + cos_angle * radius_x
            )

            y = (
                center_y
                + sin_angle * radius_y
            )

            color = self._get_cached_color(
                progress,
                color_data
            )

            self._put_pixel(
                canvas,
                int(round(x)),
                int(round(y)),
                width,
                height,
                color
            )

    def _put_pixel(
        self,
        canvas,
        x,
        y,
        width,
        height,
        color
    ):
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

        rgb = _hex_to_rgb(color)

        if rgb is None:
            canvas[y][x] = "▪"
            return

        red, green, blue = rgb

        canvas[y][x] = (
            f"\033[38;2;{red};{green};{blue}m"
            + "●"
            + ANSI_RESET
        )


def _parse_bool(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _get_gradient_colors(
    colors,
    foreground
):
    gradient_colors = []

    for key in (
        "gradient_color_1",
        "gradient_color_2",
        "gradient_color_3",
    ):
        color = _normalize_color(
            colors.get(key)
        )

        if color:
            gradient_colors.append(
                color
            )

    if not gradient_colors:
        foreground = _normalize_color(
            foreground
        )

        if foreground:
            gradient_colors.append(
                foreground
            )

    return gradient_colors


def _normalize_color(color):
    if not color:
        return None

    color = str(color).strip()

    if color.startswith("#"):
        color = color[1:]

    if len(color) == 3:
        color = "".join(
            char * 2
            for char in color
        )

    if len(color) != 6:
        return None

    try:
        int(color, 16)
    except ValueError:
        return None

    return f"#{color.lower()}"


def _hex_to_rgb(color):
    color = _normalize_color(color)

    if not color:
        return None

    color = color[1:]

    try:
        return (
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16),
        )

    except ValueError:
        return None


def _interpolate_gradient(
    colors,
    progress
):
    if not colors:
        return None

    if len(colors) == 1:
        return colors[0]

    progress = max(
        0.0,
        min(1.0, progress)
    )

    scaled = (
        progress
        * (len(colors) - 1)
    )

    index = int(
        math.floor(scaled)
    )

    if index >= len(colors) - 1:
        return colors[-1]

    local_progress = (
        scaled - index
    )

    first = _hex_to_rgb(
        colors[index]
    )

    second = _hex_to_rgb(
        colors[index + 1]
    )

    if first is None or second is None:
        return colors[index]

    red = round(
        first[0]
        + (
            second[0]
            - first[0]
        )
        * local_progress
    )

    green = round(
        first[1]
        + (
            second[1]
            - first[1]
        )
        * local_progress
    )

    blue = round(
        first[2]
        + (
            second[2]
            - first[2]
        )
        * local_progress
    )

    return (
        f"#{red:02x}"
        f"{green:02x}"
        f"{blue:02x}"
    )


def _get_mtime(path):
    if not path:
        return None

    try:
        return Path(path).stat().st_mtime

    except OSError:
        return None