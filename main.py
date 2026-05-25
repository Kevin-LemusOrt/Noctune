from spotify.player import get_current_song
from spotify.player import get_current_time

from spotify.sync import should_reset_lyrics

from lyrics.fetcher import get_synced_lyrics
from lyrics.parser import parse_lyrics

from ui.renderer import render_current_lyric

import time
import os


last_song = ""

parsed_lyrics = []

show_index = 0

last_time = 0


while True:

    try:

        song_data = get_current_song()

        if song_data != last_song:

            parts = song_data.split(" - ")

            artist = parts[0]

            song = parts[1]

            synced_lyrics = get_synced_lyrics(
                artist,
                song
            )

            if synced_lyrics is None:

                parsed_lyrics = []

            else:

                parsed_lyrics = parse_lyrics(
                    synced_lyrics
                )

            show_index = 0

            last_song = song_data

        current_time = get_current_time()

        if should_reset_lyrics(
            current_time,
            last_time
        ):

            show_index = 0

        for index, (timestamp, lyric) in enumerate(parsed_lyrics):

            if current_time >= timestamp:

                show_index = index

        render_current_lyric(
            current_time,
            parsed_lyrics,
            show_index,
            song_data
        )

        last_time = current_time

        time.sleep(0.03)

    except KeyboardInterrupt:

        os.system("tmux kill-session -t spotyterminal")

        break
    
    except Exception as e:
        
        print("Esperando Spotify...")

        time.sleep(2)