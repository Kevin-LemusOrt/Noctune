import requests


def get_synced_lyrics(artist, song):

    try:

        url = f"https://lrclib.net/api/get?artist_name={artist}&track_name={song}"

        response = requests.get(url)

        data = response.json()

        synced_lyrics = data.get("syncedLyrics")

        if synced_lyrics is None:

            return None

        return synced_lyrics

    except:

        return None