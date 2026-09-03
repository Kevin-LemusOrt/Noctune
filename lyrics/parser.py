def parse_lyrics(synced_lyrics):
    """Convierte texto LRC en una lista de tuplas (segundos, letra)."""
    # Divide el texto LRC en líneas y elimina bordes vacíos.
    lines = synced_lyrics.strip().split("\n")
    # Acumula cada marca de tiempo junto con el texto correspondiente.
    parsed_lyrics = []

    # Procesa líneas con el formato [mm:ss.xx] Letra.
    for line in lines:
        # Extrae el contenido entre corchetes, que representa el tiempo.
        timestamp = line.split("]")[0][1:]
        # Obtiene el texto situado después de la marca de tiempo.
        lyric = line.split("]")[1].strip()
        # Separa la marca de tiempo en minutos y segundos.
        minutes = int(timestamp.split(":")[0])
        seconds = float(timestamp.split(":")[1])
        # Normaliza el tiempo a segundos para compararlo con playerctl.
        total_seconds = (minutes * 60) + seconds

        # Guarda una línea ya preparada para el renderizador.
        parsed_lyrics.append((total_seconds, lyric))

    # Devuelve las líneas en el mismo orden en que aparecen en el LRC.
    return parsed_lyrics
