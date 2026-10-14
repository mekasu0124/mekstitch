# mekstitch

A chart designer for counted-thread crafts, built with **Python 3.12+ and
PySide6 (Qt 6)**. A re-imagining of the Ursa Software WinStitch workflow, with
export targets for the crafts I actually use it for: cross stitch, regular
crochet, corner-to-corner (C2C), Tunisian simple stitch, and knitting
colourwork.

Ported from a previous Tauri 2 + React 19 + Rust build: the Rust core became
`src/core/`, and the React UI became `src/app/` (Qt widgets), re-housed on the
package conventions used by the `momentum` project.

## Stack

| Layer | Tech |
|---|---|
| Shell | PySide6 (Qt for Python) 6.10+ |
| Widgets | PySide6-Fluent-Widgets (`qfluentwidgets`) |
| Core | `src/core/` — pure Python: model, history, image import, chart export |
| GUI | `src/app/` — `FluentWindow`, custom-painted `QWidget` canvas |
| Config | `python-dotenv` |

Image resampling, Floyd–Steinberg dithering and median-cut quantisation are all
built on `QImage`, so there is no third-party imaging or numerics dependency in
the core: the only runtime requirement is PySide6.

## Layout

The package follows the same shape as the `momentum` project: an entry point, a
`Config`, a single `Logic` session object, CRUD helpers under `core/crud/`, one
`QWidget` page per screen under `app/pages/`, reusable widgets under
`app/components/`, and shared background helpers under `app/utils/`.

```
src/
  main.py            entry point (`mekstitch` -> `src.main:main`)
  config.py          Config paths + metadata (mirrors momentum's `src/config.py`)
  app/               Qt GUI
    app.py             FluentWindow: nav, theme, shortcuts, cross-page signalling
    pages/             one page per nav item
      chart.py           editor: canvas, tools, project/craft/gauge/palette
      import_page.py     image -> grid mapping
      export_page.py     chart PNG + yarn-list export
      about.py           version, stack, links
    components/        reusable widgets shared by the pages
      base_page.py       page base: holds `logic`, InfoBar feedback helpers
      canvas.py          the painted chart editor (paint, tools, drag handling)
      fields.py          committing number/float/text/select field rows
      palette_panel.py   palette swatch grid + colour editor
      toolrail.py        tool picker
      readout.py         bottom readout strip
      new_chart_dialog.py
    utils/             background work (mirrors momentum's `app/utils`)
      async_helper.py    AsyncHelper over QThreadPool
      async_worker.py    QRunnable wrapper with started/finished/error signals
  core/                craft model and algorithms (pure Python, no Qt widgets)
    logic.py           the `Logic` session the UI talks to
    crud/project.py    CRUD-style `(ok, message)` operations over the chart
    model.py           Project, YarnColor, Gauge, CraftMode, default palette
    history.py         live project + snapshot undo/redo (200 steps)
    images.py          image import, dithering, median-cut palette extraction
    chart.py           PNG chart renderer + plain-text yarn list
    glyphs.py          the eight procedural chart symbols (shared by both)
    project_file.py    .wsjson save / load
  assets/            styles.qss + app icon
```

The UI never mutates the model directly: every action goes through
`Logic` / `ProjectLogic`, which returns a `(ok, message)` tuple that the page
turns into an `InfoBar` toast — the same contract `momentum` uses for its
`TaskLogic`.

## Requirements

- Python 3.12+
- PySide6

## Installation

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

## Usage

```bash
mekstitch
```

or, without installing the console script:

```bash
python -m src.main
```

Key bindings: <kbd>Ctrl</kbd>+<kbd>Z</kbd> undo, <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd>
(or <kbd>Ctrl</kbd>+<kbd>Y</kbd>) redo, <kbd>Ctrl</kbd>+<kbd>S</kbd> save,
<kbd>Ctrl</kbd>+<kbd>O</kbd> open, <kbd>Ctrl</kbd>+<kbd>N</kbd> new.

## What works today

**Grid editor** — canvas-rendered chart with zoom, and tools for pencil, eraser,
flood fill, line, rectangle (hold <kbd>Shift</kbd> to fill), and an eyedropper.
Drags that leave the canvas still commit correctly.

**Craft modes** — the same grid is reinterpreted per craft:

| Mode | Mapping |
|---|---|
| Cross Stitch | 1 cell = 1 cross stitch |
| Crochet (Single) | 1 cell = 1 single crochet |
| Corner-to-Corner | 1 block (default 5×5, adjustable) = 1 C2C pixel, blocks outlined |
| Tunisian Simple Stitch | 1 cell = 1 TSS |
| Knitting | 1 cell = 1 knit stitch (colourwork) |

**Gauge + finished size** — set stitches/rows per inch or cm; the readout strip
shows finished dimensions derived from the current gauge.

**Palette** — editable colour list with names and hex values, stitch counts per
colour, and eight procedural chart symbols cycled by palette index.

**Image import** — resize a photo onto the grid with a choice of resampling
filter, optional Floyd–Steinberg dithering, transparency handling (transparent
pixels become empty stitches), or median-cut quantisation to rebuild the palette
from the image. Runs off the GUI thread.

**Export** — printable PNG chart with grid lines, heavier rules every N cells,
C2C block outlines, and matching symbol glyphs; plus a plain-text yarn list
(colour, symbol, hex, stitch count).

**Undo/redo** — snapshot-based, 200 steps, exposed on the toolbar and the
shortcuts above.

**Project files** — `.wsjson`, pretty-printed JSON, guarded against truncated
cell buffers on load. Files written by the earlier Rust build load unchanged.

## Symbols

Symbols are drawn procedurally in `src/core/glyphs.py` rather than with a font,
so the on-screen chart and the exported PNG always agree on which symbol maps to
which colour.

## Not yet implemented

- Named/saved palettes and brand floss libraries (DMC/Anchor lookups)
- Print-to-PDF with pagination, and a legend swatch page
- Stitch-type layer beyond colour (tent, half, backstitch, French knots)
- C2C diagonal construction order and row-by-row written instructions
- Tunisian forward/return pass row instructions
- Knitting: stitch-gauge asymmetry preview and intarsia vs. stranded handling
- Import of existing image formats as a *background* trace layer

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
