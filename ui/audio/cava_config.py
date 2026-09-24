from pathlib import Path


class CavaConfig:
    """
    Lee la configuración real de Cava del usuario.

    Fuente principal:

        ~/.config/cava/config

    Si la configuración utiliza un tema:

        ~/.config/cava/themes/<theme>

    Solo se consideran activas las opciones que realmente
    están escritas en la configuración.

    Las líneas comentadas NO se consideran configuración
    del usuario.
    """

    def __init__(
        self,
        config_path=None
    ):
        self.config_path = (
            Path(config_path)
            if config_path
            else self._default_config_path()
        )

        self.sections = {}

        self.theme_name = None
        self.theme_path = None
        self.theme = {}

    # =========================================================
    # PATHS
    # =========================================================

    @staticmethod
    def _default_config_path():
        """
        Obtiene ~/.config/cava/config.

        Respeta XDG_CONFIG_HOME si existe.
        """

        xdg_config = (
            Path.home()
            / ".config"
        )

        if "XDG_CONFIG_HOME" in __import__("os").environ:

            xdg_config = Path(
                __import__("os").environ[
                    "XDG_CONFIG_HOME"
                ]
            )

        return (
            xdg_config
            / "cava"
            / "config"
        )

    # =========================================================
    # LOAD
    # =========================================================

    def load(self):
        """
        Carga la configuración principal de Cava.

        Returns:
            CavaConfig
        """

        self.sections = {}
        self.theme_name = None
        self.theme_path = None
        self.theme = {}

        if not self.config_path.exists():
            return self

        self.sections = self._parse_file(
            self.config_path
        )

        self._load_theme()

        return self

    # =========================================================
    # PARSER
    # =========================================================

    @staticmethod
    def _parse_file(path):
        """
        Parser sencillo para archivos de configuración
        tipo INI utilizados por Cava.

        Ignora:

            # comentario
            ; comentario

        y solamente toma opciones activas.
        """

        sections = {}

        current_section = None

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                for raw_line in file:

                    line = raw_line.strip()

                    # -------------------------------------------------
                    # LÍNEAS VACÍAS
                    # -------------------------------------------------

                    if not line:
                        continue

                    # -------------------------------------------------
                    # COMENTARIOS
                    # -------------------------------------------------

                    if line.startswith("#"):
                        continue

                    if line.startswith(";"):
                        continue

                    # -------------------------------------------------
                    # SECCIÓN
                    # -------------------------------------------------

                    if (
                        line.startswith("[")
                        and line.endswith("]")
                    ):

                        current_section = (
                            line[1:-1]
                            .strip()
                            .lower()
                        )

                        sections.setdefault(
                            current_section,
                            {}
                        )

                        continue

                    # -------------------------------------------------
                    # OPCIÓN
                    # -------------------------------------------------

                    if (
                        current_section is None
                        or "=" not in line
                    ):
                        continue

                    key, value = line.split(
                        "=",
                        1
                    )

                    key = key.strip().lower()
                    value = value.strip()

                    value = CavaConfig._clean_value(
                        value
                    )

                    sections[
                        current_section
                    ][key] = value

        except OSError:
            return {}

        return sections

    # =========================================================
    # VALUE CLEANING
    # =========================================================

    @staticmethod
    def _clean_value(value):
        """
        Limpia comillas externas.

        Ejemplos:

            "noctalia" -> noctalia
            'noctalia' -> noctalia
            60         -> 60
            '#afc9e6'  -> #afc9e6
        """

        if len(value) >= 2:

            if (
                value[0] == '"'
                and value[-1] == '"'
            ):
                return value[1:-1]

            if (
                value[0] == "'"
                and value[-1] == "'"
            ):
                return value[1:-1]

        return value

    # =========================================================
    # THEME
    # =========================================================

    def _load_theme(self):
        """
        Detecta el tema definido en [color]
        y carga su archivo correspondiente.
        """

        color_section = self.sections.get(
            "color",
            {}
        )

        self.theme_name = color_section.get(
            "theme"
        )

        if not self.theme_name:
            return

        if self.theme_name.lower() == "none":
            return

        themes_directory = (
            self.config_path.parent
            / "themes"
        )

        self.theme_path = (
            themes_directory
            / self.theme_name
        )

        if not self.theme_path.exists():
            self.theme_path = None
            return

        self.theme = self._parse_file(
            self.theme_path
        )

    # =========================================================
    # ACCESS
    # =========================================================

    def get(
        self,
        section,
        key,
        default=None
    ):
        """
        Obtiene una opción de la configuración principal.

        Ejemplo:

            config.get(
                "general",
                "bars"
            )
        """

        section = section.lower()
        key = key.lower()

        return self.sections.get(
            section,
            {}
        ).get(
            key,
            default
        )

    def get_theme(
        self,
        key,
        default=None
    ):
        """
        Obtiene una opción del tema activo.

        Las opciones del tema están dentro de [color].
        """

        color_section = self.theme.get(
            "color",
            {}
        )

        return color_section.get(
            key.lower(),
            default
        )

    # =========================================================
    # TYPED VALUES
    # =========================================================

    def get_int(
        self,
        section,
        key,
        default=None
    ):
        """
        Obtiene una opción como entero.
        """

        value = self.get(
            section,
            key
        )

        if value is None:
            return default

        try:
            return int(value)

        except ValueError:
            return default

    def get_float(
        self,
        section,
        key,
        default=None
    ):
        """
        Obtiene una opción como float.
        """

        value = self.get(
            section,
            key
        )

        if value is None:
            return default

        try:
            return float(value)

        except ValueError:
            return default

    def get_bool(
        self,
        section,
        key,
        default=None
    ):
        """
        Obtiene una opción booleana.

        Acepta:

            1 / 0
            true / false
            yes / no
            on / off
        """

        value = self.get(
            section,
            key
        )

        if value is None:
            return default

        value = value.lower()

        if value in (
            "1",
            "true",
            "yes",
            "on"
        ):
            return True

        if value in (
            "0",
            "false",
            "no",
            "off"
        ):
            return False

        return default

    # =========================================================
    # COLOR HELPERS
    # =========================================================

    def get_colors(self):
        """
        Devuelve los colores activos del tema.

        Si existe un tema, utiliza sus colores.

        Si no existe tema, utiliza los colores definidos
        directamente en [color] de la configuración principal.
        """

        if self.theme:

            return self.theme.get(
                "color",
                {}
            ).copy()

        return self.sections.get(
            "color",
            {}
        ).copy()

    # =========================================================
    # DEBUG
    # =========================================================

    def summary(self):
        """
        Devuelve un resumen legible de la configuración
        detectada.
        """

        return {
            "config_path": str(
                self.config_path
            ),

            "theme_name": self.theme_name,

            "theme_path": (
                str(self.theme_path)
                if self.theme_path
                else None
            ),

            "sections": self.sections.copy(),

            "theme": self.theme.copy(),

            "colors": self.get_colors()
        }