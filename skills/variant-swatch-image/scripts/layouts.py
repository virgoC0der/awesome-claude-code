"""
Six fixed swatch-overlay layouts.

Each builder takes (main_uri, swatches, bg_color) and returns full HTML
ready for the pltf-capture screenshot service.

Swatch dict shape (same as renderer):
    {"color": "#RRGGBB"}            # solid color
    {"image_path": "/path.jpg"}     # pattern — uses image as swatch fill

Layout IDs:
    bare-bl-square   bare swatches, bottom-left, horizontal, square
    bare-bl-circle   bare swatches, bottom-left, horizontal, circle
    bare-tr-square   bare swatches, top-right,   vertical,   square
    bare-tr-circle   bare swatches, top-right,   vertical,   circle
    pill-br-h        white pill, bottom-right, horizontal, max_visible=8 (+N)
    pill-br-v        white pill, bottom-right, vertical,   max_visible=8 (+N)
"""
from typing import List


PILL_MAX_VISIBLE = 8


def _swatch_div(swatch: dict, swatch_to_uri) -> str:
    if swatch.get("image_path"):
        bg = f"background-image: url('{swatch_to_uri(swatch['image_path'])}');"
    else:
        bg = f"background-color: {swatch['color']};"
    return f'<div class="swatch" style="{bg}"></div>'


def _base_css(bg_color: str) -> str:
    return f"""
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: 1000px; height: 1000px; background: white;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
  }}
  .canvas {{
    width: 1000px; height: 1000px; position: relative;
    background: {bg_color}; overflow: hidden;
  }}
  .product-area {{
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
  }}
  .product-area img {{
    max-width: 100%; max-height: 100%; object-fit: contain;
    -webkit-user-drag: none;
  }}"""


def _wrap(main_uri: str, css: str, overlay_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>{css}</style>
</head>
<body>
<div class="canvas">
  <div class="product-area">
    <img src="{main_uri}" alt="" />
  </div>
  {overlay_html}
</div>
</body>
</html>
"""


# ---------- Bare swatches (no pill background) ----------

_BARE_GROUP_POS = {
    # corner -> (position CSS, flex-direction)
    "bl": ("left: 28px; bottom: 28px;", "row"),     # bottom-left horizontal
    "tr": ("right: 28px; top: 28px;", "column"),   # top-right vertical
}


def _bare(main_uri: str, swatches: List[dict], bg_color: str,
          corner: str, shape: str, swatch_to_uri) -> str:
    pos, direction = _BARE_GROUP_POS[corner]
    radius = "50%" if shape == "circle" else "10px"
    css = _base_css(bg_color) + f"""
  .swatches {{
    position: absolute; {pos}
    display: flex; flex-direction: {direction};
    align-items: center; gap: 12px;
  }}
  .swatch {{
    width: 52px; height: 52px; border-radius: {radius};
    border: 2px solid rgba(255,255,255,0.95);
    box-shadow: 0 1px 4px rgba(0,0,0,0.18);
    background-size: cover; background-position: center;
    flex-shrink: 0;
  }}
"""
    swatches_html = "\n      ".join(_swatch_div(s, swatch_to_uri) for s in swatches)
    overlay = f'<div class="swatches">\n      {swatches_html}\n  </div>'
    return _wrap(main_uri, css, overlay)


# ---------- Pill (white rounded background, max_visible=8 + "+N") ----------

def _pill(main_uri: str, swatches: List[dict], bg_color: str,
          direction: str, swatch_to_uri) -> str:
    """direction: 'row' or 'column'."""
    visible = swatches[:PILL_MAX_VISIBLE]
    hidden = max(0, len(swatches) - PILL_MAX_VISIBLE)
    more_label = f"+{hidden}" if hidden > 0 else ""
    more_hidden_class = "" if hidden > 0 else "hidden"

    if direction == "row":
        pill_pos = "right: 28px; bottom: 28px;"
        pill_pad = "16px 24px"
        more_margin = "margin-left: 4px;"
    else:
        pill_pos = "right: 28px; bottom: 28px;"
        pill_pad = "24px 16px"
        more_margin = "margin-top: 4px;"

    css = _base_css(bg_color) + f"""
  .float {{
    position: absolute; {pill_pos}
    background: rgba(255, 255, 255, 0.96);
    border-radius: 60px;
    padding: {pill_pad};
    display: flex; flex-direction: {direction};
    align-items: center; gap: 14px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.14);
  }}
  .swatch {{
    width: 48px; height: 48px; border-radius: 50%;
    flex-shrink: 0; background-size: cover; background-position: center;
    border: 0.5px solid rgba(0, 0, 0, 0.08);
  }}
  .more {{
    font-size: 26px; font-weight: 700; color: #1c1e21;
    letter-spacing: 0.5px; {more_margin}
  }}
  .more.hidden {{ display: none; }}
"""
    swatches_html = "\n      ".join(_swatch_div(s, swatch_to_uri) for s in visible)
    overlay = (
        f'<div class="float">\n      {swatches_html}'
        f'\n      <span class="more {more_hidden_class}">{more_label}</span>'
        f'\n  </div>'
    )
    return _wrap(main_uri, css, overlay)


# ---------- Public registry ----------

LAYOUTS = {
    "bare-bl-square": lambda m, s, bg, u: _bare(m, s, bg, "bl", "square", u),
    "bare-bl-circle": lambda m, s, bg, u: _bare(m, s, bg, "bl", "circle", u),
    "bare-tr-square": lambda m, s, bg, u: _bare(m, s, bg, "tr", "square", u),
    "bare-tr-circle": lambda m, s, bg, u: _bare(m, s, bg, "tr", "circle", u),
    "pill-br-h":      lambda m, s, bg, u: _pill(m, s, bg, "row", u),
    "pill-br-v":      lambda m, s, bg, u: _pill(m, s, bg, "column", u),
}

DEFAULT_LAYOUT_IDS = list(LAYOUTS.keys())


def build_html(layout_id: str, main_uri: str, swatches: List[dict],
               bg_color: str, swatch_to_uri) -> str:
    if layout_id not in LAYOUTS:
        raise ValueError(
            f"Unknown layout '{layout_id}'. Available: {DEFAULT_LAYOUT_IDS}")
    return LAYOUTS[layout_id](main_uri, swatches, bg_color, swatch_to_uri)
