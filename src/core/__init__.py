"""mekstitch core: project model, history, image import, export."""

from .chart import ExportOptions, legend_text, render_chart
from .history import History
from .images import import_image, palette_from_image
from .logic import Logic
from .model import (
    MODE_META,
    CraftMode,
    Gauge,
    Project,
    YarnColor,
    default_palette,
    fmt_hex,
    is_valid_hex,
    parse_hex,
)
from .project_file import load_project, save_project

__version__ = "1.0.0"

__all__ = [
    "ExportOptions",
    "legend_text",
    "render_chart",
    "History",
    "import_image",
    "palette_from_image",
    "MODE_META",
    "CraftMode",
    "Gauge",
    "Project",
    "YarnColor",
    "default_palette",
    "fmt_hex",
    "is_valid_hex",
    "parse_hex",
    "load_project",
    "save_project",
    "Logic",
    "__version__",
]
