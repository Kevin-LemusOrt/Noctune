from controls.media import play_pause, next_song, previous_song


def test_play_pause():
    """Prueba el control de reproducción/pausa."""
    print("Probando play/pause...")
    play_pause()
    print("OK")


def test_next_song():
    """Prueba el control de siguiente canción."""
    print("Probando siguiente canción...")
    next_song()
    print("OK")


def test_previous_song():
    """Prueba el control de canción anterior."""
    print("Probando canción anterior...")
    previous_song()
    print("OK")


if __name__ == "__main__":
    print("=== Test de controles de Noctune ===")
    print()

    test_play_pause()
    test_next_song()
    test_previous_song()

    print()
    print("=== Pruebas terminadas ===")