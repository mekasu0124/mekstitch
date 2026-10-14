"""Image import and palette quantisation.

Ported from the image-import half of `src-tauri/src/commands.rs`. The Rust
build used the `image` crate; here we use Qt's `QImage`, which keeps the
dependency list to PySide6 alone.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from .model import Project, YarnColor, fmt_hex

RGB = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Loading / scaling
# ---------------------------------------------------------------------------


def load_rgba(path: str) -> QImage:
    """Load an image as RGBA8888. Raises FileNotFoundError on failure."""
    img = QImage(path)
    if img.isNull():
        raise FileNotFoundError(f"could not read image: {path}")
    return img.convertToFormat(QImage.Format.Format_RGBA8888)


def _buffer(img: QImage) -> tuple[bytes, int, int, int]:
    bpl = img.bytesPerLine()
    return bytes(img.constBits()), bpl, img.width(), img.height()


def _scaled(src: QImage, w: int, h: int, filter_name: str) -> QImage:
    mode = (
        Qt.TransformationMode.FastTransformation
        if filter_name == "nearest"
        else Qt.TransformationMode.SmoothTransformation
    )
    return src.scaled(
        max(1, int(w)), max(1, int(h)), Qt.AspectRatioMode.IgnoreAspectRatio, mode
    ).convertToFormat(QImage.Format.Format_RGBA8888)


def supported_image_extensions() -> list[str]:
    return ["png", "jpg", "jpeg", "gif", "bmp", "webp", "tif", "tiff"]


# ---------------------------------------------------------------------------
# Colour maths
# ---------------------------------------------------------------------------


def nearest(palette: list[RGB], rgb: tuple[float, float, float]) -> tuple[int, RGB]:
    """Nearest palette entry by squared RGB distance."""
    best, best_d = 0, float("inf")
    for i, p in enumerate(palette):
        dr = p[0] - rgb[0]
        dg = p[1] - rgb[1]
        db = p[2] - rgb[2]
        d = dr * dr + dg * dg + db * db
        if d < best_d:
            best_d, best = d, i
    return best, (palette[best] if palette else (0, 0, 0))


def median_cut(pixels: list[RGB], n: int) -> list[RGB]:
    """Median-cut colour quantisation."""
    boxes: list[list[RGB]] = [list(pixels)]
    while len(boxes) < n:
        target: tuple[int, int] | None = None
        largest = 0
        for bi, box in enumerate(boxes):
            if len(box) < 2:
                continue
            for ch in range(3):
                lo, hi = 255, 0
                for p in box:
                    v = p[ch]
                    if v < lo:
                        lo = v
                    if v > hi:
                        hi = v
                if hi - lo > largest:
                    largest = hi - lo
                    target = (bi, ch)
        if target is None or largest == 0:
            break
        bi, ch = target
        box = boxes.pop(bi)
        box.sort(key=lambda p: p[ch])
        mid = len(box) // 2
        boxes.append(box[:mid])
        boxes.append(box[mid:])

    out: list[RGB] = []
    for box in boxes:
        if not box:
            continue
        n_len = len(box)
        out.append(
            (
                sum(p[0] for p in box) // n_len,
                sum(p[1] for p in box) // n_len,
                sum(p[2] for p in box) // n_len,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Import into the grid
# ---------------------------------------------------------------------------


def import_image(
    project: Project,
    path: str,
    width: int,
    height: int,
    filter_name: str = "triangle",
    dither: bool = True,
    transparent: bool = True,
) -> None:
    """Map an image onto the current palette, replacing the grid."""
    src = load_rgba(path)
    w = max(1, int(width))
    h = max(1, int(height))
    small = _scaled(src, w, h, filter_name)
    buf, bpl, sw, sh = _buffer(small)

    w = min(w, sw)
    h = min(h, sh)

    rgb_pal = [c.rgb() for c in project.palette]
    err_cur = [[0.0, 0.0, 0.0] for _ in range(w)]
    err_next = [[0.0, 0.0, 0.0] for _ in range(w)]
    cells = [-1] * (w * h)

    for y in range(h):
        for x in range(w):
            i = y * bpl + x * 4
            a = buf[i + 3]
            idx = y * w + x
            if transparent and a < 128:
                continue

            base = [
                min(255.0, max(0.0, buf[i] + err_cur[x][0])),
                min(255.0, max(0.0, buf[i + 1] + err_cur[x][1])),
                min(255.0, max(0.0, buf[i + 2] + err_cur[x][2])),
            ]
            ci, chosen = nearest(rgb_pal, (base[0], base[1], base[2]))
            cells[idx] = ci

            if dither:
                err = (
                    base[0] - chosen[0],
                    base[1] - chosen[1],
                    base[2] - chosen[2],
                )
                _distribute(err_cur, err_next, x, w, err)

        err_cur, err_next = err_next, err_cur
        for v in err_next:
            v[0] = v[1] = v[2] = 0.0

    project.width = w
    project.height = h
    project.cells = cells


def _distribute(
    err_cur: list[list[float]],
    err_next: list[list[float]],
    x: int,
    w: int,
    e: tuple[float, float, float],
) -> None:
    """Floyd-Steinberg error diffusion across one row."""
    for buf, i, factor in (
        (err_cur, x + 1, 7.0 / 16.0),
        (err_next, x - 1, 3.0 / 16.0),
        (err_next, x, 5.0 / 16.0),
        (err_next, x + 1, 1.0 / 16.0),
    ):
        if 0 <= i < len(buf):
            buf[i][0] += e[0] * factor
            buf[i][1] += e[1] * factor
            buf[i][2] += e[2] * factor


# ---------------------------------------------------------------------------
# Palette from image
# ---------------------------------------------------------------------------


def palette_from_image(project: Project, path: str, num_colors: int) -> None:
    """Replace the palette with colours derived from an image, then remap."""
    src = load_rgba(path)
    # Subsample so quantisation stays fast on large photos.
    thumb = _scaled(src, 200, 200, "triangle")
    tbuf, tbpl, tw, th = _buffer(thumb)

    pixels: list[RGB] = []
    for y in range(th):
        for x in range(tw):
            i = y * tbpl + x * 4
            if tbuf[i + 3] >= 128:
                pixels.append((tbuf[i], tbuf[i + 1], tbuf[i + 2]))
    if not pixels:
        raise ValueError("image has no opaque pixels")

    n = max(2, min(256, int(num_colors)))
    chosen = median_cut(pixels, n)
    project.palette = [
        YarnColor(f"Colour {i + 1}", fmt_hex(rgb)) for i, rgb in enumerate(chosen)
    ]

    # Re-map using the source image at the project's own resolution so the
    # result lines up with what `import_image` would have produced.
    w, h = project.width, project.height
    resized = _scaled(src, w, h, "triangle")
    rbuf, rbpl, rw, rh = _buffer(resized)
    w, h = min(w, rw), min(h, rh)
    rgb_pal = [c.rgb() for c in project.palette]

    cells = project.cells
    if len(cells) != w * h:
        cells = [-1] * (w * h)
    for y in range(h):
        for x in range(w):
            i = y * rbpl + x * 4
            idx = y * w + x
            if rbuf[i + 3] < 128:
                cells[idx] = -1
                continue
            ci, _ = nearest(rgb_pal, (rbuf[i], rbuf[i + 1], rbuf[i + 2]))
            cells[idx] = ci

    project.width = w
    project.height = h
    project.cells = cells


def basename(path: str) -> str:
    return os.path.basename(path)
