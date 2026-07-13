def should_reset_lyrics(current_time, last_time):
    """Indica si la letra debe reiniciarse tras retroceder la reproducción."""
    # Una posición menor que la anterior significa que se buscó hacia atrás.
    if current_time < last_time:
        return True

    # Si el tiempo avanzó o no cambió, se conserva la línea actual.
    return False
