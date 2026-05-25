from subprocess import check_output
import time

lyrics = [
    (5.0, "hello"),
    (10.0, "how are you"),
    (15.0, "goodbye")
]

show_index = -1

while True:
    current_time = float(
        check_output(
            [
                "playerctl",
                "position"
            ]
        ).decode().strip()
    )

    for index, (timestamp, lyric) in enumerate(lyrics):

        if current_time >= timestamp and index > show_index:
            print(lyric)
            show_index = index
    
    time.sleep(0.1)