import os
import shutil


def render_current_lyric(
    current_time,
    parsed_lyrics,
    current_index,
    song_data
):
    """Limpia y dibuja la canción, controles y letra sincronizada."""

    # Borra el contenido previo para renderizar una nueva imagen de la interfaz.
    os.system("clear")

    # Obtiene las dimensiones disponibles de la terminal actual.
    terminal_size = shutil.get_terminal_size()
    terminal_width = terminal_size.columns
    terminal_height = terminal_size.lines

    # Muestra la canción que playerctl reporta como activa.
    print(f"Now Playing: {song_data}".center(terminal_width))
    # Separa el encabezado de la zona destinada a las letras.
    print("-" * terminal_width)
    # Enumera los atajos configurados en la sesión de tmux.
    print(
        "[P] play/pause "
        "[N] Next "
        "[B] Previous "
        "[Q] Quit "
        .center(terminal_width)
    )

    # Deja una separación visual antes del bloque de letras.
    print()

    # Reserva espacio para el encabezado y controles ya impresos.
    available_height = terminal_height - 6
    # Sitúa la letra aproximadamente en el tercio superior de la zona libre.
    top_padding = available_height // 3

    # Inserta líneas vacías para aplicar el espaciado vertical calculado.
    for _ in range(top_padding):
        print()

    # Muestra un mensaje animado mientras no haya letras disponibles.
    if len(parsed_lyrics) == 0:
        # Alterna puntos según el tiempo para señalar que la aplicación sigue activa.
        dots = int(current_time % 4)
        waiting_text = "No lyrics found" + ("." * dots)
        print(waiting_text.center(terminal_width))

    else:
        # Incluye hasta dos líneas anteriores para dar contexto a la letra actual.
        start_index = max(0, current_index - 2)
        # La línea activa es la última de las líneas visibles.
        end_index = min(len(parsed_lyrics), current_index + 1)
        visible_lyrics = parsed_lyrics[start_index:end_index]

        # Renderiza las líneas de contexto y anima únicamente la línea activa.
        for index, (timestamp, lyric) in enumerate(visible_lyrics):
            # Recupera el índice original dentro de la letra completa.
            real_index = start_index + index

            if real_index == current_index:
                # Calcula cuánto tiempo lleva activa la línea actual.
                elapsed = current_time - timestamp
                if elapsed < 0:
                    elapsed = 0

                # Usa el inicio de la siguiente línea para estimar su duración.
                if current_index + 1 < len(parsed_lyrics):
                    next_timestamp = parsed_lyrics[current_index + 1][0]
                else:
                    # La última línea recibe una duración de respaldo de cinco segundos.
                    next_timestamp = timestamp + 5

                # Evita divisiones por cero ante marcas de tiempo inválidas.
                line_duration = next_timestamp - timestamp
                if line_duration <= 0:
                    line_duration = 1

                # Determina la velocidad de aparición según longitud y duración.
                characters_per_second = (
                    len(lyric) / line_duration
                )

                # Limita la animación para mantener una lectura agradable.
                if characters_per_second < 8:
                    characters_per_second = 8
                elif characters_per_second > 22:
                    characters_per_second = 22

                # Calcula cuántos caracteres ya deben ser visibles.
                visible_characters = int(
                    elapsed * characters_per_second
                )

                # Impide cortar fuera del texto cuando la animación termina.
                if visible_characters > len(lyric):
                    visible_characters = len(lyric)

                # Recorta la letra para conseguir el efecto de escritura progresiva.
                animated_lyric = lyric[:visible_characters]
                print(animated_lyric.center(terminal_width))

            else:
                # Las líneas previas se imprimen completas como contexto.
                print(lyric.center(terminal_width))
