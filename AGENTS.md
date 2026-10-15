# AGENTS.md

Guidance for AI coding agents working in this repository. Read this before
making changes.

## Project

**mekstitch** — a desktop chart designer for counted-thread crafts (cross
stitch, single crochet, corner-to-corner, Tunisian simple stitch, and knitting
colourwork).

Built with **Python 3.12+** (developed on 3.14) and **PySide6**, using
**PySide6-Fluent-Widgets** (`qfluentwidgets`) for every control. No third-party
imaging or numerics dependency: resampling, Floyd–Steinberg dithering,
median-cut quantisation and chart export are all built on `QImage`.

This is a rewrite of an earlier Tauri 2 + React 19 + Rust build (the Rust core
became `src/core/`, the React UI became `src/app/`), laid out on the package
conventions of the sibling `momentum` project.

## Repository layout

```
src/
  main.py            entry point (`mekstitch` console script -> src.main:main)
  config.py          Config: all paths + app metadata (single source of truth)
  app/               Qt GUI
    app.py             MainWindow(FluentWindow): nav, theme, shortcuts, signalling
    pages/             one QWidget page per nav item
      chart.py           the editor (canvas + tools + project/craft/gauge/palette)
      import_page.py     image -> grid, palette-from-image
      export_page.py     chart PNG + yarn list, with live preview
      about.py
    components/        reusable widgets shared by pages
      base_page.py       BasePage: session handle + InfoBar feedback helpers
      canvas.py          StitchCanvas: the painted, interactive grid
      fields.py          committing Number/Float/Text/Select field rows
      palette_panel.py   swatch grid + colour editor
      toolrail.py        tool picker        readout.py  bottom readout strip
      new_chart_dialog.py
    utils/             background work
      async_helper.py    AsyncHelper over QThreadPool
      async_worker.py    QRunnable wrapper with started/finished/error signals
  core/                craft model + algorithms (pure Python; no Qt *widgets*)
    logic.py           Logic: the single session object the GUI talks to
    crud/project.py    ProjectLogic: every mutating operation, returns (ok, msg)
    model.py           Project, YarnColor, Gauge, CraftMode, MODE_META, palette
    history.py         History: live project + snapshot undo/redo
    images.py          image import + palette quantisation
    chart.py           chart PNG renderer + plain-text yarn list
    glyphs.py          the 8 procedural chart symbols
    project_file.py    .wsjson save / load
  assets/            styles.qss + mekstitch.png (app icon)
```

Single virtualenv: **`.venv`**. It also hosts the local tooling that runs the
repo. There is no test suite and no linter config yet.

## Commands

```bash
# setup
uv venv .venv && source .venv/bin/activate && uv pip install -e .

# run
mekstitch                 # console script
python -m src.main        # without installing

# headless verification (no display required)
QT_QPA_PLATFORM=offscreen .venv/bin/python <script.py>
```

Because there is no test suite, verify changes with a short `QT_QPA_PLATFORM=offscreen`
script that constructs the window and drives the code path you touched. Set
`QApplication.exec = lambda self: 0` if you need `main()` to return instead of
blocking. Import the package as `src.*` (that is the importable top-level
package, not a `src` layout trick).

## Architecture

Strict, deliberately shallow layers. Do not add cross-layer shortcuts.

```
main.py
  └─ Logic(Config.APP_DIR)            core/logic.py
       ├─ History                     core/history.py   (live Project + undo)
       └─ chart: ProjectLogic         core/crud/project.py
  └─ MainWindow(logic, styles)        app/app.py
       └─ pages…                      app/pages/*  (each a BasePage)
```

**Data flow for every user action**

1. A page widget emits a signal (or a button fires).
2. The page calls `self.logic.chart.<operation>(...)`.
3. `ProjectLogic` validates, then runs the change inside `History.mutate(...)`
   (which snapshots first, so undo stays consistent) and returns `(ok, message)`.
4. The page shows an `InfoBar` toast via `self.handle_error_success(...)` /
   `self.report(result)` and calls `self.refresh()`.

**Rules**

- `src/core/` must never import `PySide6.QtWidgets`. It may use `QtCore` and
  `QtGui` (drawing, `QImage`) — that is how the renderer, glyphs and image
  import work. Keep it free of window/widget concerns.
- Widgets never mutate the model directly. Every mutation goes through
  `Logic` / `ProjectLogic` and returns a `(ok, message)` tuple.
- Never raise across the widget boundary: `ProjectLogic._run(...)` converts
  exceptions into `(False, "...")`. Handlers stay exception-free.
- All model mutation must go through `History.mutate()` so it is undoable.
  Use `History.replace()` only for wholesale swaps (new/open), which resets
  history.
- Pages reach the session via `self.logic` / `self.async_helper` (set by
  `BasePage` from the parent window). Cross-page updates go through
  `MainWindow.projectChanged` and `MainWindow.notify_project_changed()`.

## Conventions

- `from __future__ import annotations` at the top of every module; use
  `X | None` style hints.
- Module and class docstrings state what the module is and, where relevant,
  which original (Rust / JSX) file it was ported from.
- Own methods and variables are `snake_case`. Qt event overrides keep Qt's
  `camelCase` and are marked `# noqa: N802`.
- Fluent stylesheet discipline: `src/assets/styles.qss` only styles the few
  custom-painted widgets (canvas viewport, swatches, readout, column). Do
  **not** add broad `QWidget { ... }` rules — they fight the Fluent theme and
  break light/dark switching.
- `Config` is the only place paths live. Do not hard-code filesystem paths.
- Import from concrete submodules (`from ..components.canvas import StitchCanvas`),
  not from the `components` package façade.

## Fluent Widgets gotchas

These have bitten before — respect them:

- `ComboBox.addItem(text, icon=None, userData=None)` — pass the value as the
  **`userData=` keyword**, never positionally (it would be read as an icon).
  Read it back with `currentData()`, select with `findData()`.
- `HyperlinkButton(url, text, parent)` — URL first, positional.
- Several Fluent widgets use `singledispatchmethod` constructors (e.g.
  `PushButton(text, parent, icon)`), so argument order differs from stock Qt.
- Prefer `FluentStyleSheet`/theming over hand-rolled styles.

## Field widgets

`components/fields.py` fields (`NumberField`, `FloatField`, `TextField`,
`SelectField`) **commit on Enter / focus-out, not per keystroke**, and their
`set_value()` is a no-op while the control has focus. When repopulating the UI
after a mutation, call `set_value()` — it will not clobber what the user is
typing. `ChartPage.refresh()` sets a `self._blocked` guard around the repopulate
block so programmatic updates don't fire mutations back into the session; keep
any new wiring inside that guard.

## Domain model

- `Project` — `name`, `width`, `height`, `mode: CraftMode`, `block_size`,
  `gauge: Gauge`, `palette: list[YarnColor]`, `cells: list[int]`.
- `cells` is a flat `width * height` list; each entry is a palette index or
  `-1` for an empty stitch. Index with `project.idx(x, y)`, guard with
  `project.in_bounds(x, y)`.
- `CraftMode` values: `crossStitch`, `crochetSingle`, `crochetC2C`,
  `tunisianSimple`, `knitting`. `MODE_META` carries the UI label/note for each.
- C2C is the only mode with a cell span > 1 (`block_size`, default 5).
- `Gauge` drives finished-size maths (`Project.finished_size()`).

## File formats

- Projects are `.wsjson` — pretty-printed JSON. The shape must stay compatible
  with the old Rust build: **camelCase keys** (`blockSize`, `stitchesPerUnit`,
  `rowsPerUnit`). `Project.from_dict` pads/trims a wrong-length `cells` buffer
  rather than raising; keep that guard.
- Chart export is PNG (`render_chart`); yarn list is plain text
  (`legend_text`).

## Async

Long work (image import, palette build) runs off the GUI thread through
`AsyncHelper.run_async(fn, ...)`, which returns an `AsyncWorker`; connect to
`worker.signals.finished` / `.error`. Follow the pattern in `import_page.py`
(disable buttons while busy, re-enable on finish/error).

## When you finish a change

1. Update `CHANGELOG.md` (Keep a Changelog format) — add to `[Unreleased]`
   under Added / Changed / Fixed / Removed.
2. Update `README.md` if the change affects layout, commands, or features.
3. Verify with an offscreen smoke script covering the code path you touched
   (construct `MainWindow`, drive the operation, assert on `logic.project`).
4. Keep the working tree free of build artefacts (`*.egg-info/`, `__pycache__/`);
   `.venv/`, `.env`, `uv.lock` and the top-level `/main.py` are gitignored.
