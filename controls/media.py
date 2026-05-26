import subprocess


def play_pause():

    subprocess.run(
        ["playerctl", "play-pause"]
    )


def next_song():

    subprocess.run(
        ["playerctl", "next"]
    )


def previous_song():

    subprocess.run(
        ["playerctl", "previous"]
    )