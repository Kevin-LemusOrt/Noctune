import sys
import time
import select
import termios
import tty

from spotify.player import get_current_song
from spotify.player import get_current_time
from spotify.sync import should_reset_lyrics

from lyrics.fetcher import get_synced_lyrics
from lyrics.parser import parse_lyrics

from controls.media import (
    play_pause,
    next_song,
    previous_song
)

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
# KEYBOARD
# =============================================================

terminal_settings = termios.tcgetattr(sys.stdin)

tty.setcbreak(sys.stdin.fileno())


def check_keyboard():
    """Comprueba si se ha pulsado una tecla y ejecuta su acción."""

    if select.select(
        [sys.stdin],
        [],
        [],
        0
    )[0]:

        key = sys.stdin.read(1).lower()

        if key == "p":

            play_pause()

        elif key == "n":

            next_song()

        elif key == "b":

            previous_song()


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
            # KEYBOARD
            # -------------------------------------------------

            check_keyboard()

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

    termios.tcsetattr(
        sys.stdin,
        termios.TCSADRAIN,
        terminal_settings
    )

    stop_visualizer()