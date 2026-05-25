def parse_lyrics(synced_lyrics):

    lines = synced_lyrics.strip().split("\n")

    parsed_lyrics = []

    for line in lines:

        timestamp = line.split("]")[0][1:]

        lyric = line.split("]")[1].strip()

        minutes = int(timestamp.split(":")[0])

        seconds = float(timestamp.split(":")[1])

        total_seconds = (minutes * 60) + seconds

        parsed_lyrics.append((total_seconds, lyric))

    return parsed_lyrics