import shutil
import textwrap

from ui.audio.cava_backend import CavaBackend
from ui.visualizers.cava import render as render_cava


_cava_backend = None


def render_current_lyric(
    current_time,
    parsed_lyrics,
    current_index,
    song_data,
    visualizer_mode="cava"
):
    """
    Renderiza la interfaz completa de Noctune.

    El renderer se encarga de:
    - dimensiones de la terminal;
    - distribución de la interfaz;
    - encabezado;
    - letras;
    - ubicación del visualizador.

    Los visualizadores se encargan únicamente
    de convertir datos en elementos visuales.
    """

    terminal_size = shutil.get_terminal_size()

    terminal_width = terminal_size.columns
    terminal_height = terminal_size.lines

    # Evita intentar dibujar una interfaz imposible de visualizar.
    if terminal_width < 40 or terminal_height < 10:
        _clear_screen()
        print("Terminal too small for Noctune.")
        return

    _clear_screen()

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    _render_header(
        song_data,
        terminal_width
    )

    # ---------------------------------------------------------
    # LAYOUT
    # ---------------------------------------------------------

    if visualizer_mode == "cava":

        _render_cava_layout(
            current_time,
            parsed_lyrics,
            current_index,
            terminal_width,
            terminal_height
        )

    elif visualizer_mode in ("vinyl", "circular"):

        _render_side_visualizer_layout(
            current_time,
            parsed_lyrics,
            current_index,
            terminal_width,
            terminal_height,
            visualizer_mode
        )

    else:

        # Si llega un modo desconocido,
        # usamos Cava como predeterminado.

        _render_cava_layout(
            current_time,
            parsed_lyrics,
            current_index,
            terminal_width,
            terminal_height
        )


# =============================================================
# SCREEN
# =============================================================

def _clear_screen():
    """Limpia la terminal usando secuencias ANSI."""

    print("\033[2J\033[H", end="")


# =============================================================
# HEADER
# =============================================================

def _render_header(song_data, terminal_width):
    """Renderiza artista y canción."""

    print(song_data.center(terminal_width))
    print("─" * terminal_width)


# =============================================================
# CAVA BACKEND
# =============================================================

def _get_cava_backend(width):
    """
    Obtiene la instancia persistente de Cava.

    Cava se inicia una sola vez y permanece activo
    mientras Noctune está funcionando.
    """

    global _cava_backend

    if _cava_backend is None:

        bars = max(
            8,
            min(64, width // 2)
        )

        _cava_backend = CavaBackend(
            bars=bars,
            framerate=30
        )

        _cava_backend.start()

    return _cava_backend


def stop_visualizer():
    """
    Detiene el backend del visualizador.

    Debe llamarse cuando Noctune termina.
    """

    global _cava_backend

    if _cava_backend is not None:

        _cava_backend.stop()

        _cava_backend = None


# =============================================================
# CAVA LAYOUT
# =============================================================

def _render_cava_layout(
    current_time,
    parsed_lyrics,
    current_index,
    terminal_width,
    terminal_height
):
    """
    Distribución para el visualizador Cava.

    Layout:

    ┌──────────────────────────────┐
    │          HEADER              │
    ├──────────────────────────────┤
    │                              │
    │            LETRAS            │
    │                              │
    ├──────────────────────────────┤
    │          VISUALIZADOR        │
    │             CAVA             │
    └──────────────────────────────┘
    """

    # Aproximadamente un tercio de la pantalla
    # queda reservado para Cava.

    visualizer_height = max(
        4,
        terminal_height // 3
    )

    lyrics_height = (
        terminal_height
        - visualizer_height
        - 2
    )

    # ---------------------------------------------------------
    # LYRICS
    # ---------------------------------------------------------

    _render_lyrics(
        current_time,
        parsed_lyrics,
        current_index,
        terminal_width,
        lyrics_height
    )

    # ---------------------------------------------------------
    # SEPARATOR
    # ---------------------------------------------------------

    print("─" * terminal_width)

    # ---------------------------------------------------------
    # VISUALIZER
    # ---------------------------------------------------------

    _render_cava_visualizer(
        terminal_width,
        visualizer_height
    )


def _render_cava_visualizer(width, height):
    """
    Obtiene un frame del backend de Cava y lo convierte
    en una visualización mediante ui.visualizers.cava.
    """

    try:

        backend = _get_cava_backend(width)

        bars = backend.read()

        lines = render_cava(
            bars,
            width,
            height
        )

        for line in lines:
            print(line)

    except Exception:

        # Si Cava falla, mantenemos la interfaz funcionando
        # en lugar de cerrar Noctune.

        for _ in range(height):
            print(" " * width)


# =============================================================
# SIDE VISUALIZER LAYOUT
# =============================================================

def _render_side_visualizer_layout(
    current_time,
    parsed_lyrics,
    current_index,
    terminal_width,
    terminal_height,
    visualizer_mode
):
    """
    Distribución para Vinyl y Circular.

    Layout:

    ┌──────────────────────┬───────────────────────┐
    │                      │                       │
    │     VISUALIZADOR     │        LETRAS         │
    │                      │                       │
    │          ◉           │      LÍNEA ACTUAL     │
    │                      │                       │
    └──────────────────────┴───────────────────────┘
    """

    # El visualizador ocupa aproximadamente un tercio
    # del ancho disponible.

    visualizer_width = max(
        18,
        terminal_width // 3
    )

    lyrics_width = (
        terminal_width
        - visualizer_width
        - 1
    )

    # ---------------------------------------------------------
    # VISUALIZER
    # ---------------------------------------------------------

    _render_side_visualizer(
        visualizer_width,
        terminal_height,
        visualizer_mode
    )

    # Separador vertical.

    print("│", end="")

    # ---------------------------------------------------------
    # LYRICS
    # ---------------------------------------------------------

    _render_lyrics(
        current_time,
        parsed_lyrics,
        current_index,
        lyrics_width,
        terminal_height,
        inline=True
    )


# =============================================================
# LYRICS
# =============================================================

def _render_lyrics(
    current_time,
    parsed_lyrics,
    current_index,
    width,
    height,
    inline=False
):
    """
    Renderiza las letras sincronizadas.

    Mantiene hasta dos líneas anteriores
    y nunca muestra líneas futuras.
    """

    if height <= 0:
        return

    if not parsed_lyrics:

        _render_waiting_message(
            current_time,
            width,
            height,
            inline
        )

        return

    # ---------------------------------------------------------
    # VISIBLE LYRICS
    # ---------------------------------------------------------

    # Mostramos:
    #
    # línea anterior
    # línea anterior
    # línea actual
    #
    # Nunca mostramos líneas futuras.

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

    # ---------------------------------------------------------
    # WRAPPING
    # ---------------------------------------------------------

    total_lines = 0

    wrapped_lines = []

    for index, (_, lyric) in enumerate(
        visible_lyrics
    ):

        real_index = start_index + index

        # Animación únicamente para la línea actual.

        if real_index == current_index:

            lyric = _animate_current_lyric(
                current_time,
                parsed_lyrics,
                current_index,
                lyric
            )

        lines = textwrap.wrap(
            lyric,
            width=max(1, width - 2)
        )

        if not lines:
            lines = [""]

        wrapped_lines.append(
            (real_index, lines)
        )

        total_lines += len(lines)

    # ---------------------------------------------------------
    # VERTICAL CENTERING
    # ---------------------------------------------------------

    top_padding = max(
        0,
        (height - total_lines) // 2
    )

    if not inline:

        for _ in range(top_padding):
            print()

    else:

        for _ in range(top_padding):
            print(
                " " * width + "│"
            )

    # ---------------------------------------------------------
    # DRAW LYRICS
    # ---------------------------------------------------------

    for real_index, lines in wrapped_lines:

        for line in lines:

            rendered_line = line.center(width)

            if inline:

                print(
                    rendered_line + "│"
                )

            else:

                print(rendered_line)


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
    Calcula la cantidad de caracteres visibles
    de la línea actual.
    """

    timestamp = parsed_lyrics[
        current_index
    ][0]

    elapsed = current_time - timestamp

    if elapsed < 0:
        elapsed = 0

    # ---------------------------------------------------------
    # LINE DURATION
    # ---------------------------------------------------------

    if current_index + 1 < len(parsed_lyrics):

        next_timestamp = parsed_lyrics[
            current_index + 1
        ][0]

    else:

        next_timestamp = timestamp + 5

    line_duration = (
        next_timestamp
        - timestamp
    )

    if line_duration <= 0:
        line_duration = 1

    # ---------------------------------------------------------
    # CHARACTERS PER SECOND
    # ---------------------------------------------------------

    characters_per_second = (
        len(lyric)
        / line_duration
    )

    # Evitamos animaciones demasiado lentas
    # o demasiado rápidas.

    characters_per_second = max(
        8,
        min(22, characters_per_second)
    )

    # ---------------------------------------------------------
    # VISIBLE CHARACTERS
    # ---------------------------------------------------------

    visible_characters = int(
        elapsed
        * characters_per_second
    )

    visible_characters = min(
        visible_characters,
        len(lyric)
    )

    return lyric[
        :visible_characters
    ]


# =============================================================
# WAITING MESSAGE
# =============================================================

def _render_waiting_message(
    current_time,
    width,
    height,
    inline=False
):
    """Muestra un mensaje mientras no existen letras."""

    dots = int(
        current_time % 4
    )

    waiting_text = (
        "No lyrics found"
        + ("." * dots)
    )

    top_padding = max(
        0,
        (height - 1) // 2
    )

    if inline:

        for _ in range(top_padding):

            print(
                " " * width + "│"
            )

        print(
            waiting_text.center(width)
            + "│"
        )

    else:

        for _ in range(top_padding):
            print()

        print(
            waiting_text.center(width)
        )


# =============================================================
# SIDE VISUALIZER PLACEHOLDER
# =============================================================

def _render_side_visualizer(
    width,
    height,
    visualizer_mode
):
    """
    Reserva temporalmente el área lateral.

    Vinyl y Circular todavía no están conectados.
    """

    label = (
        f"[ {visualizer_mode.upper()} ]"
    )

    top_padding = max(
        0,
        (height - 1) // 2
    )

    for row in range(height):

        if row == top_padding:

            print(
                label.center(width),
                end=""
            )

        else:

            print(
                " " * width,
                end=""
            )