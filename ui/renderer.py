import os
import shutil


def render_current_lyric(
    current_time,
    parsed_lyrics,
    current_index,
    song_data
):

    os.system("clear")

    terminal_height = shutil.get_terminal_size().lines

    lyrics_height = terminal_height // 2

    print(f"Now Playing: {song_data}")

    print("-" * 50)

    empty_lines = lyrics_height // 2

    for _ in range(empty_lines):

        print()

    if len(parsed_lyrics) == 0:

        dots = int(current_time % 4)

        waiting_text = "No lyrics found" + ("." * dots)

        print(waiting_text.center(80))

    else:

        if current_index >= len(parsed_lyrics):

            current_index = len(parsed_lyrics) - 1

        current_timestamp, current_lyric = parsed_lyrics[current_index]

        elapsed = current_time - current_timestamp

        if elapsed < 0:

            elapsed = 0

        characters_per_second = 25

        visible_characters = int(elapsed * characters_per_second)

        if visible_characters > len(current_lyric):

            visible_characters = len(current_lyric)

        animated_lyric = current_lyric[:visible_characters]

        print(animated_lyric.center(80))

    remaining_lines = lyrics_height - empty_lines

    for _ in range(remaining_lines):

        print()

    print("-" * 50)

    print("CAVA GOES HERE")