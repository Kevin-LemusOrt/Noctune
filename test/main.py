from subprocess import check_output
import time
import os

last_song = ""

while True:

    current_song = check_output(
        [
            "playerctl",
            "metadata",
            "--format",
            "{{artist}} - {{title}}"
        ]
    ).decode().strip()

    if current_song != last_song:

        os.system("clear")

        print(current_song)

        last_song = current_song

    time.sleep(1)