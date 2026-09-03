import subprocess


def play_pause():
    """Alterna entre reproducción y pausa en el reproductor activo."""
    # Delega la acción multimedia a playerctl.
    subprocess.run(["playerctl", "play-pause"])


def next_song():
    """Pasa a la siguiente canción del reproductor activo."""
    # Envía el comando de siguiente pista a playerctl.
    subprocess.run(["playerctl", "next"])


def previous_song():
    """Vuelve a la canción anterior del reproductor activo."""
    # Envía el comando de pista anterior a playerctl.
    subprocess.run(["playerctl", "previous"])
