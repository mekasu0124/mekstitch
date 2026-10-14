"""Core data model for a mekstitch project.

A project is a grid of cells. Each cell either holds an index into the project
palette, or is empty (`-1`). The same grid is reinterpreted depending on
`CraftMode`.

Ported from `src-tauri/src/model.rs`. The JSON shape stays compatible with the
old Rust build's `.wsjson` files (camelCase keys).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class CraftMode(str, Enum):
    """Which craft the chart is being interpreted for."""

    CROSS_STITCH = "crossStitch"
    CROCHET_SINGLE = "crochetSingle"
    CROCHET_C2C = "crochetC2C"
    TUNISIAN_SIMPLE = "tunisianSimple"
    KNITTING = "knitting"


@dataclass
class YarnColor:
    """A single colour in the working palette."""

    name: str
    hex: str  # "#RRGGBB"

    def rgb(self) -> tuple[int, int, int]:
        """RGB triple, falling back to mid-grey on a malformed hex string."""
        return parse_hex(self.hex) or (128, 128, 128)

    def to_dict(self) -> dict:
        return {"name": self.name, "hex": self.hex}

    @classmethod
    def from_dict(cls, d: dict) -> "YarnColor":
        return cls(str(d.get("name", "")), str(d.get("hex", "#000000")))


@dataclass
class Gauge:
    """How many stitches / rows make up one unit of measurement."""

    stitches_per_unit: float = 4.5
    rows_per_unit: float = 5.5
    unit: str = "in"

    def to_dict(self) -> dict:
        return {
            "stitchesPerUnit": self.stitches_per_unit,
            "rowsPerUnit": self.rows_per_unit,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Gauge":
        return cls(
            float(d.get("stitchesPerUnit", 4.5)),
            float(d.get("rowsPerUnit", 5.5)),
            str(d.get("unit", "in")),
        )


@dataclass
class Project:
    """A complete chart."""

    name: str = "Untitled"
    width: int = 60
    height: int = 60
    mode: CraftMode = CraftMode.CROSS_STITCH
    block_size: int = 5
    gauge: Gauge = field(default_factory=Gauge)
    palette: list[YarnColor] = field(default_factory=list)
    cells: list[int] = field(default_factory=list)

    # -- construction ------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        width: int,
        height: int,
        mode: CraftMode = CraftMode.CROSS_STITCH,
    ) -> "Project":
        width = max(1, int(width))
        height = max(1, int(height))
        return cls(
            name=name,
            width=width,
            height=height,
            mode=mode,
            block_size=5,
            gauge=Gauge(),
            palette=default_palette(),
            cells=[-1] * (width * height),
        )

    # -- indexing ----------------------------------------------------------

    def idx(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> int:
        return self.cells[self.idx(x, y)]

    def set(self, x: int, y: int, color: int) -> None:
        self.cells[self.idx(x, y)] = color

    # -- derived -----------------------------------------------------------

    def cell_span(self) -> int:
        """Cells that make up one finished stitch. C2C works in blocks."""
        if self.mode == CraftMode.CROCHET_C2C:
            return max(1, self.block_size)
        return 1

    def finished_size(self) -> tuple[float, float]:
        """Finished width/height in `gauge.unit`."""
        span = float(self.cell_span())
        w = (self.width / span) / max(0.01, self.gauge.stitches_per_unit)
        h = (self.height / span) / max(0.01, self.gauge.rows_per_unit)
        return w, h

    def color_counts(self) -> list[int]:
        """Count of stitches per palette entry."""
        counts = [0] * len(self.palette)
        for c in self.cells:
            if 0 <= c < len(counts):
                counts[c] += 1
        return counts

    # -- mutations ---------------------------------------------------------

    def resize(self, width: int, height: int) -> None:
        """Resize the canvas, keeping the art anchored at the top-left."""
        width = max(1, int(width))
        height = max(1, int(height))
        cells = [-1] * (width * height)
        copy_w = min(width, self.width)
        copy_h = min(height, self.height)
        for y in range(copy_h):
            src = y * self.width
            dst = y * width
            cells[dst : dst + copy_w] = self.cells[src : src + copy_w]
        self.width = width
        self.height = height
        self.cells = cells

    def flood_fill(self, x: int, y: int, color: int) -> None:
        """Four-connected flood fill from `(x, y)` with `color`."""
        if not self.in_bounds(x, y):
            return
        target = self.get(x, y)
        if target == color:
            return
        w, h = self.width, self.height
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not self.in_bounds(cx, cy):
                continue
            if self.get(cx, cy) != target:
                continue
            self.set(cx, cy, color)
            if cx > 0:
                stack.append((cx - 1, cy))
            if cy > 0:
                stack.append((cx, cy - 1))
            if cx + 1 < w:
                stack.append((cx + 1, cy))
            if cy + 1 < h:
                stack.append((cx, cy + 1))

    # -- serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "mode": self.mode.value,
            "blockSize": self.block_size,
            "gauge": self.gauge.to_dict(),
            "palette": [c.to_dict() for c in self.palette],
            "cells": list(self.cells),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        width = max(1, int(d.get("width", 1)))
        height = max(1, int(d.get("height", 1)))
        try:
            mode = CraftMode(d.get("mode", CraftMode.CROSS_STITCH.value))
        except ValueError:
            mode = CraftMode.CROSS_STITCH
        cells = [int(c) for c in d.get("cells", [])]
        expected = width * height
        if len(cells) != expected:
            # Guard against a corrupt/edited file whose buffer is the wrong size.
            cells = (cells + [-1] * expected)[:expected]
        palette = [YarnColor.from_dict(c) for c in d.get("palette", [])]
        return cls(
            name=str(d.get("name", "Untitled")),
            width=width,
            height=height,
            mode=mode,
            block_size=int(d.get("blockSize", 5)),
            gauge=Gauge.from_dict(d.get("gauge", {})),
            palette=palette or default_palette(),
            cells=cells,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_hex(hex_str: str) -> tuple[int, int, int] | None:
    """Parse `#RRGGBB` or `RRGGBB` into an RGB triple."""
    h = str(hex_str).strip().lstrip("#")
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def is_valid_hex(hex_str: str) -> bool:
    return parse_hex(hex_str) is not None


def fmt_hex(rgb: Iterable[int]) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def default_palette() -> list[YarnColor]:
    """A small starter palette loosely based on common DMC floss colours."""
    return [
        YarnColor("310 Black", "#000000"),
        YarnColor("B5200 White", "#FFFFFF"),
        YarnColor("666 Red", "#E31C25"),
        YarnColor("321 Deep Red", "#C72B3B"),
        YarnColor("972 Gold", "#FFB500"),
        YarnColor("704 Green", "#7BC043"),
        YarnColor("702 Kelly", "#3E9B4F"),
        YarnColor("3843 Blue", "#1F8AC0"),
        YarnColor("796 Navy", "#17497E"),
        YarnColor("553 Violet", "#A05EB5"),
        YarnColor("3607 Pink", "#E56AA5"),
        YarnColor("3776 Peach", "#E8A87C"),
        YarnColor("738 Tan", "#E3C39D"),
        YarnColor("951 Cream", "#F7E7CE"),
        YarnColor("3799 Grey", "#5A5A5A"),
        YarnColor("415 Light Grey", "#C9C9C9"),
        YarnColor("434 Brown", "#7B4B2A"),
        YarnColor("801 Coffee", "#6B4423"),
        YarnColor("550 Purple", "#6A2C70"),
        YarnColor("726 Gold", "#F2C75C"),
    ]


# UI-friendly metadata for the craft modes (mirrors src/types.js MODES).
MODE_META: list[dict] = [
    {
        "id": CraftMode.CROSS_STITCH,
        "label": "Cross Stitch",
        "short": "Cross",
        "span": 1,
        "note": "1 cell = 1 cross stitch",
    },
    {
        "id": CraftMode.CROCHET_SINGLE,
        "label": "Crochet (Single)",
        "short": "Crochet",
        "span": 1,
        "note": "1 cell = 1 single crochet",
    },
    {
        "id": CraftMode.CROCHET_C2C,
        "label": "Corner-to-Corner",
        "short": "C2C",
        "span": 5,
        "note": "1 block = 1 C2C pixel (ch 3 + 3 dc)",
    },
    {
        "id": CraftMode.TUNISIAN_SIMPLE,
        "label": "Tunisian Simple Stitch",
        "short": "Tunisian",
        "span": 1,
        "note": "1 cell = 1 TSS; rows work forward then return",
    },
    {
        "id": CraftMode.KNITTING,
        "label": "Knitting",
        "short": "Knit",
        "span": 1,
        "note": "1 cell = 1 knit stitch (colourwork)",
    },
]
