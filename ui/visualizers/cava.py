from ui.audio.cava_config import CavaConfig


BAR_LEVELS = " ▁▂▃▄▅▆▇█"
ANSI_RESET = "\033[0m"


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
        # NORMALIZACIÓN
        # ---------------------------------------------------------

        bars = _normalize_bars(
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

    def colorize(
        self,
        lines,
        width
    ):
        """Aplica color sin alterar los caracteres ni el ancho visible."""

        colors = self.config.get_colors()
        foreground = colors.get("foreground")

        if not foreground:
            foreground = colors.get("color")

        if not foreground:
            return lines

        colored_lines = []

        for line in lines:
            result = []

            for character in line[:width]:
                if character == " ":
                    result.append(character)
                    continue

                result.extend([
                    _ansi_fg(foreground),
                    character,
                    ANSI_RESET
                ])

            colored_lines.append(
                "".join(result)
                + (" " * max(0, width - len(line)))
            )

        return colored_lines

    def _smooth_bars(
        self,
        bars
    ):
        """
        Suaviza los cambios entre frames.
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

            if current > previous:

                value = (
                    previous * 0.25
                    + current * 0.75
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
    """Colorea líneas ya ajustadas, conservando su contenido visible."""

    if not hasattr(render, "_visualizer"):
        render._visualizer = CavaVisualizer()

    return render._visualizer.colorize(
        lines,
        width
    )


def _ansi_fg(color):
    color = str(color).strip()

    if color.startswith("#"):
        color = color[1:]

    if len(color) != 6:
        return ""

    try:
        red = int(color[0:2], 16)
        green = int(color[2:4], 16)
        blue = int(color[4:6], 16)
    except ValueError:
        return ""

    return f"\033[38;2;{red};{green};{blue}m"


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

    # ---------------------------------------------------------
    # ESPACIO UTILIZADO POR CADA BARRA
    # ---------------------------------------------------------

    cell_width = (
        bar_width
        + bar_spacing
    )

    # Cantidad máxima de barras que caben.
    #
    # El +bar_spacing permite que la última barra
    # no necesite espacio de separación después de ella.
    max_bars = (
        width
        + bar_spacing
    ) // cell_width

    max_bars = max(
        1,
        max_bars
    )

    # ---------------------------------------------------------
    # DEMASIADAS BARRAS
    # ---------------------------------------------------------

    if len(bars) > max_bars:

        return _downsample(
            bars,
            max_bars
        )

    # ---------------------------------------------------------
    # POCAS BARRAS
    #
    # Interpolamos para llenar horizontalmente
    # el espacio disponible.
    # ---------------------------------------------------------

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
    # LIMITAR ALTURA SEGÚN max_height DE CAVA
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
    # ESPACIO TOTAL NECESARIO
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
    # DIBUJAR CADA BARRA
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
                    lines[y][current_x] = "█"

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