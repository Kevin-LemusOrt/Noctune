import threading
import os

from controls.media import (
    play_pause,
    next_song,
    previous_song,
)

def command_listener():

    while True:

        command = input().lower()

        if command == "p":

            play_pause()
        
        elif command == "n":

            next_song()

        elif command == "b":

            previous_song()

        elif command == "q":

            os.system("tmux kill-session -t spotyterminal")

            break

def start_listener():

    thread = threading.Thread(target=command_listener, daemon=True)

    thread.start()