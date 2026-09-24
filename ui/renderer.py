import os
import shutil
import textwrap


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
    - espacio reservado para el visualizador.

    Los visualizadores reales se integrarán posteriormente desde
    ui/visualizers/.
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

    _render_header(song_data, terminal_width)

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
        # Si llega un modo desconocido, usamos Cava como
        # comportamiento predeterminado.
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
# CAVA LAYOUT
# =============================================================

def _render_cava_layout(
    current_time,
    parsed_lyrics,
    current_index,
    terminal_width,
    terminal_height
):

    # Reservamos aproximadamente el 30% inferior
    # para el futuro visualizador.
    visualizer_height = max(4, terminal_height // 3)

    lyrics_height = terminal_height - visualizer_height - 2

    _render_lyrics(
        current_time,
        parsed_lyrics,
        current_index,
        terminal_width,
        lyrics_height
    )

    print("─" * terminal_width)

    _render_visualizer_placeholder(
        terminal_width,
        visualizer_height,
        "cava"
    )


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

    # El visualizador ocupa aproximadamente un tercio.
    visualizer_width = max(18, terminal_width // 3)

    lyrics_width = terminal_width - visualizer_width - 1

    _render_side_visualizer(
        visualizer_width,
        terminal_height,
        visualizer_mode
    )

    print("│", end="")

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

    Mantiene hasta dos líneas anteriores y nunca muestra
    líneas futuras.
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

    # Solo mostramos contexto anterior + línea actual.
    start_index = max(0, current_index - 2)
    end_index = min(len(parsed_lyrics), current_index + 1)

    visible_lyrics = parsed_lyrics[start_index:end_index]

    # Calcula el espacio vertical disponible.
    total_lines = 0

    wrapped_lines = []

    for index, (_, lyric) in enumerate(visible_lyrics):
        real_index = start_index + index

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

        wrapped_lines.append((real_index, lines))
        total_lines += len(lines)

    top_padding = max(0, (height - total_lines) // 2)

    if not inline:
        for _ in range(top_padding):
            print()

    else:
        # En layout lateral el padding se imprime dentro del panel.
        for _ in range(top_padding):
            print(" " * width + "│")


    for real_index, lines in wrapped_lines:
        for line in lines:

            if real_index == current_index:
                rendered_line = line.center(width)
            else:
                rendered_line = line.center(width)

            if inline:
                print(rendered_line + "│")
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
    """Calcula la cantidad de caracteres visibles de la línea actual."""

    timestamp = parsed_lyrics[current_index][0]

    elapsed = current_time - timestamp

    if elapsed < 0:
        elapsed = 0

    # Duración estimada hasta la siguiente línea.
    if current_index + 1 < len(parsed_lyrics):
        next_timestamp = parsed_lyrics[current_index + 1][0]
    else:
        next_timestamp = timestamp + 5

    line_duration = next_timestamp - timestamp

    if line_duration <= 0:
        line_duration = 1

    characters_per_second = len(lyric) / line_duration

    # Límites para evitar animaciones demasiado lentas
    # o demasiado rápidas.
    characters_per_second = max(
        8,
        min(22, characters_per_second)
    )

    visible_characters = int(
        elapsed * characters_per_second
    )

    visible_characters = min(
        visible_characters,
        len(lyric)
    )

    return lyric[:visible_characters]


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

    dots = int(current_time % 4)

    waiting_text = "No lyrics found" + ("." * dots)

    top_padding = max(
        0,
        (height - 1) // 2
    )

    if inline:
        for _ in range(top_padding):
            print(" " * width + "│")

        print(waiting_text.center(width) + "│")

    else:
        for _ in range(top_padding):
            print()

        print(waiting_text.center(width))


# =============================================================
# VISUALIZER PLACEHOLDER
# =============================================================

def _render_visualizer_placeholder(
    width,
    height,
    visualizer_mode
):
    """
    Reserva el área del visualizador.

    Actualmente solo representa el espacio que ocupará
    el visualizador real.

    Posteriormente esta función será reemplazada por llamadas
    a ui.visualizers.cava, ui.visualizers.circular y
    ui.visualizers.vinyl.
    """

    label = f"[ {visualizer_mode.upper()} ]"

    top_padding = max(
        0,
        (height - 1) // 2
    )

    for _ in range(top_padding):
        print()

    print(label.center(width))


# =============================================================
# SIDE VISUALIZER PLACEHOLDER
# =============================================================

def _render_side_visualizer(
    width,
    height,
    visualizer_mode
):
    """
    Reserva el área lateral del visualizador.

    Posteriormente será reemplazada por el visualizador
    correspondiente.
    """

    label = f"[ {visualizer_mode.upper()} ]"

    top_padding = max(
        0,
        (height - 1) // 2
    )

    for row in range(height):

        if row == top_padding:
            print(label.center(width), end="")
        else:
            print(" " * width, end="")