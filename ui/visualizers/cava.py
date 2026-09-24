# Caracteres utilizados para representar diferentes alturas.
BAR_LEVELS = " ▁▂▃▄▅▆▇█"


def render(bars, width, height):
    """
    Convierte los datos del espectro en una visualización de barras.

    Parameters:
        bars: lista de valores entre 0.0 y 1.0
        width: ancho disponible
        height: alto disponible

    Returns:
        list[str]: líneas que forman el visualizador.
    """

    if width <= 0 or height <= 0:
        return []

    if not bars:
        return [" " * width for _ in range(height)]

    bars = _fit_bars_to_width(bars, width)

    lines = [
        [" "] * width
        for _ in range(height)
    ]

    for x, value in enumerate(bars):

        value = max(0.0, min(1.0, value))

        exact_height = value * height
        full_rows = int(exact_height)

        remainder = exact_height - full_rows

        # Parte completa de la barra.
        for offset in range(full_rows):
            y = height - 1 - offset

            if y >= 0:
                lines[y][x] = "█"

        # Parte parcial superior.
        if full_rows < height and remainder > 0:

            level = int(
                remainder * (len(BAR_LEVELS) - 1)
            )

            y = height - 1 - full_rows

            if y >= 0:
                lines[y][x] = BAR_LEVELS[level]

    return [
        "".join(line)
        for line in lines
    ]


def _fit_bars_to_width(bars, width):
    """
    Ajusta la cantidad de barras al ancho disponible.

    Si Cava entrega más barras que espacio disponible,
    agrupamos.

    Si entrega menos, las centramos.
    """

    if len(bars) == width:
        return bars

    if len(bars) > width:
        return _downsample(bars, width)

    padding = width - len(bars)

    left = padding // 2
    right = padding - left

    return (
        [0.0] * left
        + bars
        + [0.0] * right
    )


def _downsample(values, target_size):
    """Reduce una lista agrupando valores."""

    result = []

    source_size = len(values)

    for index in range(target_size):

        start = int(
            index * source_size / target_size
        )

        end = int(
            (index + 1) * source_size / target_size
        )

        if end <= start:
            end = start + 1

        chunk = values[start:end]

        result.append(max(chunk))

    return result