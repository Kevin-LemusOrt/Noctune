from subprocess import check_output


def get_current_song():
    """Devuelve artista y título de la canción activa mediante playerctl."""
    # Ejecuta playerctl y define el formato que consume la aplicación.
    song_data = check_output(
        ["playerctl", "metadata", "--format", "{{artist}} - {{title}}"]
    ).decode().strip()

    # Elimina el salto de línea final de la salida del comando.
    return song_data


def get_current_time():
    """Devuelve la posición de reproducción actual en segundos."""
    # Convierte la salida textual de playerctl en un número decimal.
    current_time = float(check_output(["playerctl", "position"]).decode().strip())

    # Entrega el tiempo usado para sincronizar la letra.
    return current_time
