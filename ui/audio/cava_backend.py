import os
import shutil
import subprocess
import tempfile
import threading

from .cava_config import CavaConfig


class CavaBackend:
    """
    Backend de audio para Noctune.

    Cava analiza el audio y entrega frames mediante stdout.

    La configuración del usuario se obtiene desde:

        ~/.config/cava/config

    Noctune solamente añade la configuración necesaria
    para poder recibir los datos RAW por stdout.
    """

    def __init__(
        self,
        bars=None,
        framerate=None
    ):
        self.config = CavaConfig().load()

        # -----------------------------------------------------
        # CONFIGURACIÓN DE CAVA
        # -----------------------------------------------------

        configured_bars = self.config.get_int(
            "general",
            "bars"
        )

        configured_framerate = self.config.get_int(
            "general",
            "framerate"
        )

        # Si el usuario configuró estos valores,
        # utilizarlos.
        #
        # Si no, conservar los valores internos actuales
        # de Noctune temporalmente.

        self.bars = max(
            1,
            bars
            if bars is not None
            else (
                configured_bars
                if configured_bars is not None
                and configured_bars > 0
                else 32
            )
        )

        self.framerate = max(
            1,
            framerate
            if framerate is not None
            else (
                configured_framerate
                if configured_framerate is not None
                and configured_framerate > 0
                else 60
            )
        )

        # -----------------------------------------------------
        # PROCESS
        # -----------------------------------------------------

        self.process = None
        self.config_path = None

        self._latest_frame = None
        self._running = False
        self._reader_thread = None
        self._lock = threading.Lock()

    # =========================================================
    # LIFECYCLE
    # =========================================================

    def start(self):
        """
        Inicia Cava y su lector de frames.
        """

        if self.process is not None:
            return

        if shutil.which("cava") is None:
            raise RuntimeError(
                "Cava was not found. Please install cava."
            )

        self.config_path = self._create_config()

        self.process = subprocess.Popen(
            [
                "cava",
                "-p",
                self.config_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        self._running = True

        self._reader_thread = threading.Thread(
            target=self._read_loop,
            daemon=True
        )

        self._reader_thread.start()

    def stop(self):
        """
        Detiene Cava y limpia sus recursos.
        """

        self._running = False

        if self.process is not None:

            if self.process.poll() is None:

                self.process.terminate()

                try:

                    self.process.wait(
                        timeout=1
                    )

                except subprocess.TimeoutExpired:

                    self.process.kill()
                    self.process.wait()

            self.process = None

        if self._reader_thread is not None:

            self._reader_thread.join(
                timeout=1
            )

            self._reader_thread = None

        self._remove_config()

        with self._lock:

            self._latest_frame = None

    # =========================================================
    # DATA
    # =========================================================

    def read(self):
        """
        Devuelve inmediatamente el último frame disponible.

        Nunca espera a Cava.
        """

        with self._lock:

            if self._latest_frame is None:
                return None

            return self._latest_frame.copy()

    # =========================================================
    # READER
    # =========================================================

    def _read_loop(self):
        """
        Lee continuamente stdout de Cava en segundo plano.

        El renderer no participa en esta lectura.
        """

        if self.process is None:
            return

        if self.process.stdout is None:
            return

        while self._running:

            line = self.process.stdout.readline()

            if not line:
                break

            frame = self._parse_frame(
                line
            )

            if frame is not None:

                with self._lock:

                    self._latest_frame = frame

    # =========================================================
    # CONFIG
    # =========================================================

    def _create_config(self):
        """
        Crea una configuración temporal exclusiva
        para la instancia de Cava utilizada por Noctune.

        Los parámetros de audio importantes se obtienen
        desde la configuración real del usuario.

        La salida RAW por stdout es propia de Noctune.
        """

        # -----------------------------------------------------
        # VALORES DEL USUARIO
        # -----------------------------------------------------

        input_method = self.config.get(
            "input",
            "method"
        )

        input_source = self.config.get(
            "input",
            "source"
        )

        output_channels = self.config.get(
            "output",
            "channels"
        )

        mono_option = self.config.get(
            "output",
            "mono_option"
        )

        reverse = self.config.get(
            "output",
            "reverse"
        )

        # -----------------------------------------------------
        # CONFIGURACIÓN BASE
        # -----------------------------------------------------

        config_lines = [
            "[general]",
            "",
            f"framerate = {self.framerate}",
            f"bars = {self.bars}",
            "autosens = 1",
            "sensitivity = 100",
            "",
            "[input]",
            "",
        ]

        # -----------------------------------------------------
        # INPUT
        # -----------------------------------------------------

        if input_method is not None:

            config_lines.append(
                f"method = {input_method}"
            )

        else:

            # Mantener el método que ya utilizaba
            # Noctune cuando el usuario no especifica uno.

            config_lines.append(
                "method = pipewire"
            )

        if input_source is not None:

            config_lines.append(
                f"source = {input_source}"
            )

        else:

            config_lines.append(
                "source = auto"
            )

        # -----------------------------------------------------
        # OUTPUT
        # -----------------------------------------------------

        config_lines.extend([
            "",
            "[output]",
            "",
            "method = raw",
            "raw_target = /dev/stdout",
            "data_format = ascii",
            "ascii_max_range = 1000",
            "bar_delimiter = 59",
            "frame_delimiter = 10",
        ])

        # -----------------------------------------------------
        # CHANNELS
        # -----------------------------------------------------

        if output_channels is not None:

            config_lines.append(
                f"channels = {output_channels}"
            )

        else:

            config_lines.append(
                "channels = mono"
            )

        if mono_option is not None:

            config_lines.append(
                f"mono_option = {mono_option}"
            )

        else:

            config_lines.append(
                "mono_option = average"
            )

        if reverse is not None:

            config_lines.append(
                f"reverse = {reverse}"
            )

        else:

            config_lines.append(
                "reverse = 0"
            )

        # -----------------------------------------------------
        # SMOOTHING
        # -----------------------------------------------------

        config_lines.extend([
            "",
            "[smoothing]",
            "",
            "noise_reduction = 0",
            ""
        ])

        config = "\n".join(
            config_lines
        )

        # -----------------------------------------------------
        # TEMP FILE
        # -----------------------------------------------------

        file_descriptor, path = tempfile.mkstemp(
            prefix="noctune-cava-",
            suffix=".conf"
        )

        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(config)

        return path

    # =========================================================
    # PARSING
    # =========================================================

    def _parse_frame(self, line):
        """
        Convierte un frame ASCII de Cava
        en valores normalizados.

        Ejemplo:

            120;340;700;1000;820;...

        Resultado:

            [0.12, 0.34, 0.70, 1.0, 0.82, ...]
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
            max(
                0.0,
                min(
                    1.0,
                    value / maximum
                )
            )
            for value in values
        ]

    # =========================================================
    # CLEANUP
    # =========================================================

    def _remove_config(self):
        """
        Elimina la configuración temporal.
        """

        if self.config_path is None:
            return

        try:

            os.remove(
                self.config_path
            )

        except FileNotFoundError:
            pass

        self.config_path = None

    # =========================================================
    # CONTEXT MANAGER
    # =========================================================

    def __enter__(self):

        self.start()

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):

        self.stop()