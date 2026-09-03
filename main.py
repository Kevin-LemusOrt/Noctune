from spotify.player import get_current_song
from spotify.player import get_current_time
from spotify.sync import should_reset_lyrics
from lyrics.fetcher import get_synced_lyrics
from lyrics.parser import parse_lyrics
from ui.renderer import render_current_lyric

import time


# Guarda la canción anterior para solicitar letras solo cuando esta cambia.
last_song = ""
# Contiene las líneas como tuplas: (segundo de inicio, texto).
parsed_lyrics = []
# Indica el índice de la línea que debe mostrarse como activa.
show_index = 0
# Conserva la posición previa para detectar retrocesos de reproducción.
last_time = 0


# Bucle principal: consulta el reproductor y actualiza la interfaz.
while True:
    try:
        # Obtiene la canción actual con el formato "artista - título".
        song_data = get_current_song()

        # Descarga letras nuevas solo si cambió la canción.
        if song_data != last_song:
            # Separa los datos necesarios para buscar la letra en LRCLIB.
            parts = song_data.split(" - ")
            artist = parts[0]
            song = parts[1]

            # Solicita la versión LRC, que incluye las marcas de tiempo.
            synced_lyrics = get_synced_lyrics(artist, song)

            # Una respuesta sin letra conserva una lista vacía para el renderizador.
            if synced_lyrics is None:
                parsed_lyrics = []
            else:
                # Convierte el texto LRC a marcas de tiempo en segundos.
                parsed_lyrics = parse_lyrics(synced_lyrics)

            # La nueva canción inicia mostrando la primera línea disponible.
            show_index = 0
            last_song = song_data

        # Lee la posición actual del reproductor en segundos.
        current_time = get_current_time()

        # Reinicia el índice si el usuario retrocedió en la canción.
        if should_reset_lyrics(current_time, last_time):
            show_index = 0

        # Selecciona la última línea cuyo tiempo de inicio ya fue alcanzado.
        for index, (timestamp, lyric) in enumerate(parsed_lyrics):
            if current_time >= timestamp:
                show_index = index

        # Redibuja la interfaz con el progreso y letra actuales.
        render_current_lyric(current_time, parsed_lyrics, show_index, song_data)

        # Actualiza la referencia temporal para la siguiente iteración.
        last_time = current_time
        # Limita la actualización a unas 33 imágenes por segundo.
        time.sleep(0.03)

    except Exception:
        # Muestra un estado de espera si no hay reproductor, red o letra disponible.
        render_current_lyric(0, [], 0, "Esperando canción o Spotify")
        # Evita reintentos agresivos mientras persista el error.
        time.sleep(1)
