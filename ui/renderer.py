import os
import shutil


def render_current_lyric(
    current_time,
    parsed_lyrics,
    current_index,
    song_data
):

    os.system("clear")

    terminal_size = shutil.get_terminal_size()

    terminal_width = terminal_size.columns

    terminal_height = terminal_size.lines

    print(f"Now Playing: {song_data}".center(terminal_width))

    print("-" * terminal_width)

    print(
        "[P] play/pause "
        "[N] Next "
        "[B] Previous "
        "[Q] Quit "
        .center(terminal_width)
    )

    print()

    available_height = terminal_height - 6

    top_padding = available_height // 3

    for _ in range(top_padding):

        print()

    if len(parsed_lyrics) == 0:

        dots = int(current_time % 4)

        waiting_text = "No lyrics found" + ("." * dots)

        print(waiting_text.center(terminal_width))

    else:

        start_index = max(0, current_index - 2)

        end_index = min(len(parsed_lyrics), current_index + 1)

        visible_lyrics = parsed_lyrics[start_index:end_index]

        for index, (timestamp, lyric) in enumerate(visible_lyrics):

            real_index = start_index + index

            if real_index == current_index:

                elapsed = current_time - timestamp

                if elapsed < 0:

                    elapsed = 0

                if current_index + 1 < len(parsed_lyrics):

                    next_timestamp = parsed_lyrics[current_index + 1][0]

                else:

                    next_timestamp = timestamp + 5

                line_duration = next_timestamp - timestamp

                if line_duration <= 0:

                    line_duration = 1

                characters_per_second = (
                    len(lyric) / line_duration
                ) * 0.85

                visible_characters = int(
                    elapsed * characters_per_second
                )

                if visible_characters > len(lyric):

                    visible_characters = len(lyric)

                animated_lyric = lyric[:visible_characters]

                print(animated_lyric.center(terminal_width))

            else:

                print(lyric.center(terminal_width))