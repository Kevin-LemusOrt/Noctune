import os
import shutil
import subprocess
import tempfile


class CavaBackend:
    """
    Gestiona una instancia interna de Cava.

    Cava funciona como backend de análisis de audio:
    - No dibuja nada en la terminal.
    - No controla la interfaz.
    - Produce valores numéricos del espectro.
    """

    def __init__(self, bars=32, framerate=60):
        self.bars = max(1, bars)
        self.framerate = max(1, framerate)

        self.process = None
        self.config_path = None

    # ---------------------------------------------------------
    # LIFECYCLE
    # ---------------------------------------------------------

    def start(self):
        """Inicia la instancia interna de Cava."""

        if self.process is not None:
            return

        if shutil.which("cava") is None:
            raise RuntimeError(
                "Cava was not found. Please install cava."
            )

        self.config_path = self._create_config()

        self.process = subprocess.Popen(
            ["cava", "-p", self.config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1
        )

    def stop(self):
        """Detiene Cava y elimina su configuración temporal."""

        if self.process is not None:

            if self.process.poll() is None:
                self.process.terminate()

                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()

            self.process = None

        self._remove_config()

    # ---------------------------------------------------------
    # DATA
    # ---------------------------------------------------------

    def read(self):
        """
        Lee un frame del espectro.

        Devuelve:
            list[float] | None

        Los valores están normalizados entre 0.0 y 1.0.
        """

        if self.process is None:
            return None

        if self.process.stdout is None:
            return None

        line = self.process.stdout.readline()

        if not line:
            return None

        return self._parse_frame(line)

    # ---------------------------------------------------------
    # CONFIG
    # ---------------------------------------------------------

    def _create_config(self):
        """
        Crea una configuración temporal exclusiva para Noctune.

        No modifica ~/.config/cava/config.
        """

        config = f"""
[general]

framerate = {self.framerate}
bars = {self.bars}
autosens = 1
sensitivity = 100

[input]

method = pipewire
source = auto

[output]

method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 1000
bar_delimiter = 59
frame_delimiter = 10

channels = mono
mono_option = average
reverse = 0

[smoothing]

noise_reduction = 65
"""

        file_descriptor, path = tempfile.mkstemp(
            prefix="noctune-cava-",
            suffix=".conf"
        )

        with os.fdopen(file_descriptor, "w") as file:
            file.write(config)

        return path

    # ---------------------------------------------------------
    # PARSING
    # ---------------------------------------------------------

    def _parse_frame(self, line):
        """
        Convierte una línea ASCII de Cava en valores normalizados.

        Cava produce algo conceptualmente parecido a:

            120;340;700;1000;820;...

        """

        line = line.strip()

        if not line:
            return None

        try:
            values = [
                int(value)
                for value in line.split(";")
                if value
            ]
        except ValueError:
            return None

        if not values:
            return None

        maximum = 1000

        return [
            max(0.0, min(1.0, value / maximum))
            for value in values
        ]

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------

    def _remove_config(self):
        """Elimina la configuración temporal de Cava."""

        if self.config_path is None:
            return

        try:
            os.remove(self.config_path)
        except FileNotFoundError:
            pass

        self.config_path = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()