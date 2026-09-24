import shutil
import re
import sys
import textwrap

from ui.audio.cava_backend import CavaBackend
from ui.visualizers.cava import (
    render as render_cava,
    colorize as colorize_cava
)


_cava_backend = None
_cava_width = None
_ANSI_PATTERN = re.compile(r"\033\[[0-?]*[ -/]*[@-~]")


# =============================================================
# MAIN RENDERER
# =============================================================

def render_current_lyric(
    current_time,
    parsed_lyrics,
    current_index,
    song_data,
    visualizer_mode="cava"
):
    """
    Renderiza la interfaz completa de Noctune.

    La interfaz se adapta al tamaño actual
    de la terminal.
    """

    terminal_size = shutil.get_terminal_size(
        fallback=(80, 24)
    )

    width = terminal_size.columns
    height = terminal_size.lines

    if width < 40 or height < 8:

        _draw_small_terminal(
            width,
            height
        )

        return

    frame = _build_frame(
        current_time=current_time,
        parsed_lyrics=parsed_lyrics,
        current_index=current_index,
        song_data=song_data,
        width=width,
        height=height,
        visualizer_mode=visualizer_mode
    )

    _draw_frame(
        frame
    )


# =============================================================
# FRAME
# =============================================================

def _build_frame(
    current_time,
    parsed_lyrics,
    current_index,
    song_data,
    width,
    height,
    visualizer_mode
):
    """
    Construye el frame completo antes de dibujarlo.
    """

    frame = [
        " " * width
        for _ in range(height)
    ]

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    frame[0] = _fit_line(
        _center_line(
            song_data,
            width
        ),
        width
    )

    if height > 1:

        frame[1] = (
            "─" * width
        )

    # ---------------------------------------------------------
    # LAYOUT
    # ---------------------------------------------------------

    if visualizer_mode == "cava":

        _build_cava_layout(
            frame,
            current_time,
            parsed_lyrics,
            current_index,
            width,
            height
        )

    else:

        _build_cava_layout(
            frame,
            current_time,
            parsed_lyrics,
            current_index,
            width,
            height
        )

    return frame


# =============================================================
# CAVA LAYOUT
# =============================================================

def _build_cava_layout(
    frame,
    current_time,
    parsed_lyrics,
    current_index,
    width,
    height
):
    """
    Distribución actual:

        Header
        ──────
        Letras
        ──────
        Cava

    La distribución vertical se conserva.
    """

    lyrics_start = 2

    separator_height = 1

    # ---------------------------------------------------------
    # DISTRIBUCIÓN VERTICAL
    # ---------------------------------------------------------

    visualizer_height = max(
        4,
        height // 3
    )

    lyrics_height = (
        height
        - 2
        - separator_height
        - visualizer_height
    )

    if lyrics_height < 3:

        lyrics_height = 3

        visualizer_height = (
            height
            - 2
            - separator_height
            - lyrics_height
        )

    visualizer_height = max(
        1,
        visualizer_height
    )

    separator_row = (
        lyrics_start
        + lyrics_height
    )

    visualizer_start = (
        separator_row
        + separator_height
    )

    # ---------------------------------------------------------
    # LETRAS
    # ---------------------------------------------------------

    lyrics_lines = _build_lyrics(
        current_time,
        parsed_lyrics,
        current_index,
        width,
        lyrics_height
    )

    for index, line in enumerate(
        lyrics_lines
    ):

        row = (
            lyrics_start
            + index
        )

        if row >= separator_row:
            break

        if row >= height:
            break

        frame[row] = _fit_line(
            line,
            width
        )

    # ---------------------------------------------------------
    # SEPARADOR
    # ---------------------------------------------------------

    if separator_row < height:

        frame[separator_row] = (
            "─" * width
        )

    # ---------------------------------------------------------
    # CAVA
    # ---------------------------------------------------------

    cava_lines = _render_cava(
        width,
        visualizer_height
    )

    cava_lines = [
        _fit_line(line, width)
        for line in cava_lines[:visualizer_height]
    ]

    cava_lines = colorize_cava(
        cava_lines,
        width
    )

    for index, line in enumerate(cava_lines):

        row = visualizer_start + index

        if row >= height:
            break

        frame[row] = line


# =============================================================
# LYRICS
# =============================================================

def _build_lyrics(
    current_time,
    parsed_lyrics,
    current_index,
    width,
    height
):
    """
    Construye las líneas visibles de la letra.

    Se muestran:
        - hasta 2 líneas anteriores
        - línea actual

    No se muestran líneas futuras.
    """

    if height <= 0:
        return []

    # ---------------------------------------------------------
    # SIN LETRA
    # ---------------------------------------------------------

    if not parsed_lyrics:

        dots = int(
            current_time % 4
        )

        waiting_text = (
            "No lyrics found"
            + "." * dots
        )

        return _center_vertical(
            [
                _center_line(
                    waiting_text,
                    width
                )
            ],
            height
        )

    # ---------------------------------------------------------
    # VALIDAR ÍNDICE
    # ---------------------------------------------------------

    current_index = max(
        0,
        min(
            current_index,
            len(parsed_lyrics) - 1
        )
    )

    # ---------------------------------------------------------
    # LÍNEAS VISIBLES
    # ---------------------------------------------------------

    start_index = max(
        0,
        current_index - 2
    )

    end_index = min(
        len(parsed_lyrics),
        current_index + 1
    )

    visible_lyrics = parsed_lyrics[
        start_index:end_index
    ]

    lines = []

    # ---------------------------------------------------------
    # PROCESAR LETRAS
    # ---------------------------------------------------------

    for index, (_, lyric) in enumerate(
        visible_lyrics
    ):

        real_index = (
            start_index
            + index
        )

        if real_index == current_index:

            lyric = _animate_current_lyric(
                current_time,
                parsed_lyrics,
                current_index,
                lyric
            )

        wrapped = textwrap.wrap(
            lyric,
            width=max(
                1,
                width - 2
            )
        )

        if not wrapped:
            wrapped = [""]

        for line in wrapped:

            lines.append(
                _center_line(
                    line,
                    width
                )
            )

    return _center_vertical(
        lines,
        height
    )


# =============================================================
# LYRIC ANIMATION
# =============================================================

def _animate_current_lyric(
    current_time,
    parsed_lyrics,
    current_index,
    lyric
):
    """
    Revela progresivamente la línea actual.
    """

    timestamp = parsed_lyrics[
        current_index
    ][0]

    elapsed = (
        current_time
        - timestamp
    )

    if elapsed < 0:
        elapsed = 0

    if current_index + 1 < len(
        parsed_lyrics
    ):

        next_timestamp = parsed_lyrics[
            current_index + 1
        ][0]

    else:

        next_timestamp = (
            timestamp + 5
        )

    line_duration = (
        next_timestamp
        - timestamp
    )

    if line_duration <= 0:
        line_duration = 1

    characters_per_second = (
        len(lyric)
        / line_duration
    )

    characters_per_second = max(
        8,
        min(
            22,
            characters_per_second
        )
    )

    visible_characters = int(
        elapsed
        * characters_per_second
    )

    visible_characters = max(
        0,
        min(
            visible_characters,
            len(lyric)
        )
    )

    return lyric[
        :visible_characters
    ]


# =============================================================
# CAVA BACKEND
# =============================================================

def _get_cava_backend(width):
    """
    Obtiene la instancia global de Cava.

    La configuración de barras y framerate
    ahora pertenece exclusivamente a CavaBackend,
    que la obtiene desde ~/.config/cava/config.
    """

    global _cava_backend
    global _cava_width

    # ---------------------------------------------------------
    # PRIMER INICIO
    # ---------------------------------------------------------

    if (
        _cava_backend is None
        or _cava_width != width
    ):

        if _cava_backend is not None:
            _cava_backend.stop()

        _cava_backend = CavaBackend(
            bars=max(1, width)
        )

        _cava_backend.start()

        _cava_width = width

    return _cava_backend


def _render_cava(
    width,
    height
):
    """
    Obtiene el último frame disponible de Cava
    y lo convierte en líneas.
    """

    if width <= 0 or height <= 0:
        return []

    try:

        backend = _get_cava_backend(width)

        bars = backend.read()

        # Todavía no existe un frame.

        if bars is None:

            return [
                " " * width
                for _ in range(height)
            ]

        lines = render_cava(
            bars,
            width,
            height
        )

        return lines[:height]

    except Exception:

        return [
            " " * width
            for _ in range(height)
        ]


# =============================================================
# STOP VISUALIZER
# =============================================================

def stop_visualizer():
    """
    Detiene Cava y libera sus recursos.
    """

    global _cava_backend
    global _cava_width

    if _cava_backend is not None:

        _cava_backend.stop()

        _cava_backend = None

    _cava_width = None


# =============================================================
# FRAME DRAWING
# =============================================================

def _draw_frame(
    frame
):
    """
    Dibuja el frame utilizando ANSI.

    No limpia toda la terminal en cada actualización,
    evitando parpadeos.
    """

    if not frame:
        return

    output = []

    for row, line in enumerate(
        frame,
        start=1
    ):

        output.append(
            f"\033[{row};1H"
        )

        output.append(
            "\033[2K"
        )

        output.append(
            line
        )

    sys.stdout.write(
        "".join(output)
    )

    sys.stdout.flush()


# =============================================================
# TEXT HELPERS
# =============================================================

def _center_line(
    text,
    width
):
    """
    Centra horizontalmente un texto.
    """

    if width <= 0:
        return ""

    text = str(text)

    if len(text) > width:

        text = text[:width]

    padding = (
        width - len(text)
    )

    left = padding // 2
    right = padding - left

    return (
        (" " * left)
        + text
        + (" " * right)
    )


def _fit_line(
    text,
    width
):
    """
    Garantiza que una línea tenga exactamente
    el ancho de la terminal.
    """

    if width <= 0:
        return ""

    text = str(text)
    visible_length = len(
        _ANSI_PATTERN.sub("", text)
    )

    if visible_length > width:
        result = []
        visible_length = 0

        for token in re.split(
            "(" + _ANSI_PATTERN.pattern + ")",
            text
        ):
            if not token:
                continue

            if _ANSI_PATTERN.fullmatch(token):
                result.append(token)
                continue

            remaining = width - visible_length

            if remaining <= 0:
                break

            result.append(token[:remaining])
            visible_length += min(
                len(token),
                remaining
            )

        return "".join(result)

    return (
        text
        + (
            " "
            * (
                width
                - visible_length
            )
        )
    )


def _center_vertical(
    lines,
    height
):
    """
    Centra un bloque verticalmente.
    """

    if height <= 0:
        return []

    lines = list(lines)

    if len(lines) >= height:

        return lines[-height:]

    remaining = (
        height
        - len(lines)
    )

    top = remaining // 2
    bottom = remaining - top

    return (
        ([""] * top)
        + lines
        + ([""] * bottom)
    )


# =============================================================
# SMALL TERMINAL
# =============================================================

def _draw_small_terminal(
    width,
    height
):
    """
    Mensaje para terminales demasiado pequeñas.
    """

    output = "\033[H"

    message = (
        "Terminal too small for Noctune."
    )

    if width > 0:

        message = _center_line(
            message,
            width
        )

    total_rows = max(
        1,
        height
    )

    for row in range(
        1,
        total_rows + 1
    ):

        output += (
            f"\033[{row};1H"
            "\033[2K"
        )

        if row == total_rows:

            output += message

    sys.stdout.write(
        output
    )

    sys.stdout.flush()