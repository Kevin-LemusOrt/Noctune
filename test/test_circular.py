import shutil
import sys
import time

from ui.audio.cava_backend import CavaBackend
from ui.visualizers.circular import CircularVisualizer


def draw_frame(lines):
    sys.stdout.write("\033[H")

    for line in lines:
        sys.stdout.write(
            "\033[2K"
            + line
            + "\n"
        )

    sys.stdout.flush()


def main():
    backend = CavaBackend()
    visualizer = CircularVisualizer()

    backend.start()

    try:
        while True:
            terminal = shutil.get_terminal_size(
                fallback=(80, 24)
            )

            width = terminal.columns
            height = terminal.lines - 1

            if width <= 0 or height <= 0:
                time.sleep(0.05)
                continue

            bars = backend.read()

            if bars is None:
                lines = [
                    " " * width
                    for _ in range(height)
                ]
            else:
                lines = visualizer.render(
                    bars,
                    width,
                    height
                )

            draw_frame(lines)

            time.sleep(0.03)

    except KeyboardInterrupt:
        pass

    finally:
        backend.stop()

        sys.stdout.write(
            "\033[0m"
            "\033[2J"
            "\033[H"
        )
        sys.stdout.flush()


if __name__ == "__main__":
    main()