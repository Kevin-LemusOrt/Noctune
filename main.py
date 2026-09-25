import sys
import time

from spotify.player import get_current_song
from spotify.player import get_current_time
from spotify.sync import should_reset_lyrics

from lyrics.fetcher import get_synced_lyrics
from lyrics.parser import parse_lyrics

from ui.renderer import (
    render_current_lyric,
    stop_visualizer
)


# =============================================================
# VISUALIZER MODE
# =============================================================

visualizer_mode = "cava"

if "-c" in sys.argv or "--circle" in sys.argv:
    visualizer_mode = "circle"


# =============================================================
# STATE
# =============================================================

last_song = ""

parsed_lyrics = []

show_index = 0

last_time = 0


# =============================================================
# MAIN LOOP
# =============================================================

try:

    while True:

        try:

            # -------------------------------------------------
            # CURRENT SONG
            # -------------------------------------------------

            song_data = get_current_song()

            if song_data != last_song:

                parts = song_data.split(
                    " - ",
                    1
                )

                if len(parts) == 2:

                    artist = parts[0]

                    song = parts[1]

                else:

                    artist = ""

                    song = song_data

                # ---------------------------------------------
                # FETCH LYRICS
                # ---------------------------------------------

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

            # -------------------------------------------------
            # CURRENT TIME
            # -------------------------------------------------

            current_time = get_current_time()

            # -------------------------------------------------
            # RESET LYRICS
            # -------------------------------------------------

            if should_reset_lyrics(
                current_time,
                last_time
            ):

                show_index = 0

            # -------------------------------------------------
            # FIND CURRENT LYRIC
            # -------------------------------------------------

            for index, (
                timestamp,
                lyric
            ) in enumerate(
                parsed_lyrics
            ):

                if current_time >= timestamp:

                    show_index = index

            # -------------------------------------------------
            # RENDER
            # -------------------------------------------------

            render_current_lyric(
                current_time,
                parsed_lyrics,
                show_index,
                song_data,
                visualizer_mode=visualizer_mode
            )

            # -------------------------------------------------
            # SAVE TIME
            # -------------------------------------------------

            last_time = current_time

            time.sleep(
                0.03
            )

        # =====================================================
        # KEYBOARD INTERRUPT
        # =====================================================

        except KeyboardInterrupt:

            raise

        # =====================================================
        # RUNTIME ERROR
        # =====================================================

        except Exception:

            render_current_lyric(
                0,
                [],
                0,
                "Esperando canción o Spotify",
                visualizer_mode=visualizer_mode
            )

            time.sleep(
                1
            )


# =============================================================
# EXIT
# =============================================================

except KeyboardInterrupt:

    stop_visualizer()

finally:

    stop_visualizer()