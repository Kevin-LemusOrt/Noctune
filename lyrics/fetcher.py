import requests


def get_synced_lyrics(artist, song):
    """Busca en LRCLIB la letra sincronizada de una canción."""
    try:
        # Construye la consulta con el artista y título del reproductor.
        url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={song}"
        # Solicita los datos de la canción a la API pública de LRCLIB.
        response = requests.get(url)
        # Convierte la respuesta JSON en un diccionario de Python.
        data = response.json()
        # Extrae la letra LRC, que contiene una marca de tiempo por línea.
        synced_lyrics = data.get("syncedLyrics")

        # Indica que no hay letra sincronizada cuando la API no la proporciona.
        if synced_lyrics is None:
            return None

        # Devuelve el texto LRC para que el parser lo procese.
        return synced_lyrics
    except:
        # Evita detener la interfaz ante errores de red o respuestas inválidas.
        return None
