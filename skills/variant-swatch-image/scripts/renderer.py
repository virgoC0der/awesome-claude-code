"""
Template renderer.

Fills the HTML template with main image + swatches, then renders to PNG
via the AfterShip pltf-capture screenshot service.

Requires AM_API_KEY environment variable.

Swatch shape:
    {
        "color": "#RRGGBB",         # OR
        "image_path": "/path.jpg",  # for patterns/prints
        "selected": False,
    }

Output is 1:1 (1000x1000) with a SHEIN-style floating pill at bottom-right.
If max_visible is set and exceeded, remainder shows as "+N".
"""
from pathlib import Path
from typing import List, Optional
import base64
import io
import json
import os
import urllib.error
import urllib.request
import sys
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from layouts import build_html as _build_layout_html  # noqa: E402
from layouts import DEFAULT_LAYOUT_IDS  # noqa: E402


_TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "template.html"
_SCREENSHOT_API = "http://pltf-capture.as-in.io/v1/internal/screenshots"


def _to_data_uri(image_path: str, crop_center: bool = False) -> str:
    p = Path(image_path)
    ext = p.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg",
            "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "image/png")

    if crop_center:
        img = Image.open(p).convert("RGB")
        w, h = img.size
        side = min(w, h) // 4
        cx, cy = w // 2, h // 2
        img = img.crop((cx - side, cy - side, cx + side, cy + side))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        mime = "image/png"
        raw = buf.getvalue()
    else:
        raw = p.read_bytes()

    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _swatch_html(swatch: dict) -> str:
    if swatch.get("image_path"):
        bg = f"background-image: url('{_to_data_uri(swatch['image_path'], crop_center=True)}');"
    else:
        bg = f"background-color: {swatch['color']};"
    return f'<div class="swatch" style="{bg}"></div>'


def fill_template(
    main_image_path: str,
    swatches: List[dict],
    bg_color: str = "#FFFFFF",
    max_visible: Optional[int] = None,
) -> str:
    """
    Build the filled HTML string. Useful for debugging without an API call.

    If max_visible is set and len(swatches) > max_visible, only the first
    max_visible swatches render; the remainder is shown as "+N".
    """
    template = _TEMPLATE_PATH.read_text()
    main_uri = _to_data_uri(main_image_path)

    visible = swatches
    hidden_count = 0
    if max_visible is not None and len(swatches) > max_visible:
        visible = swatches[:max_visible]
        hidden_count = len(swatches) - max_visible

    swatches_html = "\n      ".join(_swatch_html(s) for s in visible)
    more_label = f"+{hidden_count}" if hidden_count > 0 else ""
    more_hidden_class = "" if hidden_count > 0 else "hidden"

    return (template
            .replace("__BG_COLOR__", bg_color)
            .replace("__MAIN_IMAGE__", main_uri)
            .replace("__SWATCHES__", swatches_html)
            .replace("__MORE_LABEL__", more_label)
            .replace("__MORE_HIDDEN_CLASS__", more_hidden_class))


def screenshot(
    html: str,
    width: int = 1000,
    wait_seconds: float = 1.0,
) -> dict:
    """
    POST to AfterShip pltf-capture. Returns {"image_url", "file_id"}.
    Raises RuntimeError on missing AM_API_KEY or non-success response.
    """
    api_key = os.environ.get("AM_API_KEY")
    if not api_key:
        raise RuntimeError("AM_API_KEY env var is required")

    payload = {
        "page": {
            "html": html,
            "width": width,
            "wait_seconds": wait_seconds,
        },
        "output": {"public": True},
        "format": "png",
        "full_page": True,
    }
    req = urllib.request.Request(
        _SCREENSHOT_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "am-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Screenshot API HTTP {e.code}: {body}") from e

    # pltf-capture returns meta.code == 20000 on success (not 200).
    meta_code = data.get("meta", {}).get("code")
    if meta_code not in (200, 20000):
        raise RuntimeError(f"Screenshot API non-success: {data}")
    return data["data"]


def _download(url: str, dest: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        Path(dest).write_bytes(resp.read())
    return dest


def _crop_square(path: str) -> None:
    """In-place crop top-aligned to a square. pltf-capture's full_page
    screenshot may overshoot the declared 1000px height by a few px."""
    im = Image.open(path)
    w, h = im.size
    if w == h:
        return
    side = min(w, h)
    im.crop((0, 0, side, side)).save(path)


def _pattern_swatch_uri(image_path: str) -> str:
    """Center-cropped data URI for pattern swatches."""
    return _to_data_uri(image_path, crop_center=True)


def render_layouts(
    main_image_path: str,
    swatches: List[dict],
    layouts: Optional[List[str]] = None,
    output_dir: Optional[str] = None,
    bg_color: str = "#FFFFFF",
    width: int = 1000,
    wait_seconds: float = 1.0,
) -> List[dict]:
    """
    Render the same product across multiple fixed layouts.

    Args:
        layouts: list of layout IDs (see layouts.LAYOUTS). Defaults to all six.
        output_dir: if set, each PNG is downloaded to {output_dir}/{layout}.png
                    and cropped to 1:1.

    Returns:
        list of {"layout", "url", "file_id", "local_path"} — one per layout.
    """
    layout_ids = layouts or DEFAULT_LAYOUT_IDS
    main_uri = _to_data_uri(main_image_path)
    out_dir = Path(output_dir) if output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for layout_id in layout_ids:
        html = _build_layout_html(
            layout_id, main_uri, swatches, bg_color, _pattern_swatch_uri)
        api = screenshot(html, width=width, wait_seconds=wait_seconds)
        entry = {
            "layout": layout_id,
            "url": api["image_url"],
            "file_id": api["file_id"],
            "local_path": None,
        }
        if out_dir:
            local = out_dir / f"{layout_id}.png"
            _download(api["image_url"], str(local))
            _crop_square(str(local))
            entry["local_path"] = str(local)
        results.append(entry)
    return results


def render_listing_image(
    main_image_path: str,
    swatches: List[dict],
    output_png: Optional[str] = None,
    bg_color: str = "#FFFFFF",
    width: int = 1000,
    wait_seconds: float = 1.0,
    max_visible: Optional[int] = None,
) -> dict:
    """
    End-to-end: fill template -> call screenshot API -> optionally download PNG.

    Args:
        max_visible: cap visible swatches; remainder shown as "+N".

    Returns:
        {
            "url":        "https://files.aftership.com/v1/capture/...png",
            "file_id":    "9f3a1c2e...",
            "local_path": "/path/to/out.png" or None,
        }
    """
    html = fill_template(
        main_image_path, swatches, bg_color, max_visible=max_visible)
    api_result = screenshot(html, width=width, wait_seconds=wait_seconds)

    out = {
        "url": api_result["image_url"],
        "file_id": api_result["file_id"],
        "local_path": None,
    }
    if output_png:
        out["local_path"] = _download(api_result["image_url"], output_png)
        _crop_square(output_png)
    return out
