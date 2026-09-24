BAR_LEVELS = " ▁▂▃▄▅▆▇█"


class CavaVisualizer:
    """
    Visualizador de espectro para Noctune.

    Recibe los datos generados por Cava y se encarga
    únicamente de convertirlos en caracteres.
    """

    def __init__(self):
        self.previous_bars = []

    def render(
        self,
        bars,
        width,
        height
    ):
        """
        Genera las líneas del visualizador.

        Parameters:
            bars: valores entre 0.0 y 1.0
            width: ancho disponible
            height: alto disponible

        Returns:
            list[str]
        """

        if width <= 0 or height <= 0:
            return []

        if not bars:
            return [
                " " * width
                for _ in range(height)
            ]

        # Ajustar las barras al ancho actual.
        bars = _fit_bars_to_width(
            bars,
            width
        )

        # Suavizar el movimiento.
        bars = self._smooth_bars(
            bars
        )

        # Aprovechar mejor la altura disponible.
        bars = _normalize_bars(
            bars
        )

        return _draw_bars(
            bars,
            width,
            height
        )

    # =========================================================
    # SMOOTHING
    # =========================================================

    def _smooth_bars(
        self,
        bars
    ):
        """
        Suaviza el movimiento de las barras.

        Si cambia la cantidad de barras debido a un resize
        de la terminal, se reinicia el historial.
        """

        # -----------------------------------------------------
        # PRIMER FRAME O CAMBIO DE TAMAÑO
        # -----------------------------------------------------

        if (
            not self.previous_bars
            or len(self.previous_bars) != len(bars)
        ):

            self.previous_bars = bars.copy()

            return bars

        # -----------------------------------------------------
        # SUAVIZADO NORMAL
        # -----------------------------------------------------

        smoothed = []

        for current, previous in zip(
            bars,
            self.previous_bars
        ):

            if current > previous:

                # Ataque rápido.

                value = (
                    previous * 0.25
                    + current * 0.75
                )

            else:

                # Caída progresiva.

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
# PUBLIC RENDER FUNCTION
# =============================================================

def render(
    bars,
    width,
    height
):
    """
    Función pública utilizada por renderer.py.

    Mantiene una única instancia del visualizador
    para conservar el suavizado entre frames.
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


# =============================================================
# BAR FITTING
# =============================================================

def _fit_bars_to_width(
    bars,
    width
):
    """
    Ajusta las barras al ancho de la terminal.

    Si hay más barras que columnas:
        reduce usando el máximo de cada grupo.

    Si hay menos barras:
        las interpola para ocupar todo el ancho.
    """

    if width <= 0:
        return []

    if not bars:
        return [0.0] * width

    if len(bars) == width:
        return bars

    # ---------------------------------------------------------
    # DEMASIADAS BARRAS
    # ---------------------------------------------------------

    if len(bars) > width:

        return _downsample(
            bars,
            width
        )

    # ---------------------------------------------------------
    # MENOS BARRAS QUE COLUMNAS
    # ---------------------------------------------------------

    if len(bars) == 1:

        return bars * width

    result = []

    source_size = len(bars)

    for index in range(width):

        position = (
            index
            * (source_size - 1)
            / (width - 1)
        )

        left = int(position)

        right = min(
            left + 1,
            source_size - 1
        )

        fraction = (
            position - left
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
    Reduce una lista de barras conservando
    el máximo de cada grupo.
    """

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


# =============================================================
# NORMALIZATION
# =============================================================

def _normalize_bars(
    bars
):
    """
    Escala el frame para aprovechar mejor
    la altura disponible.

    La barra más alta llega a 1.0 y las demás
    conservan su proporción relativa.
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
# DRAWING
# =============================================================

def _draw_bars(
    bars,
    width,
    height
):
    """
    Convierte las barras normalizadas
    en caracteres de terminal.
    """

    lines = [
        [" "] * width
        for _ in range(height)
    ]

    for x, value in enumerate(
        bars
    ):

        if x >= width:
            break

        value = max(
            0.0,
            min(
                1.0,
                value
            )
        )

        exact_height = (
            value * height
        )

        full_rows = int(
            exact_height
        )

        remainder = (
            exact_height
            - full_rows
        )

        # -----------------------------------------------------
        # FULL BLOCKS
        # -----------------------------------------------------

        for offset in range(
            full_rows
        ):

            y = (
                height
                - 1
                - offset
            )

            if y >= 0:

                lines[y][x] = "█"

        # -----------------------------------------------------
        # PARTIAL BLOCK
        # -----------------------------------------------------

        if (
            full_rows < height
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

                lines[y][x] = (
                    BAR_LEVELS[level]
                )

    return [
        "".join(line)
        for line in lines
    ]
