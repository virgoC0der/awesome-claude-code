"""
Parse Shopify PDP HTML for option-level swatch metadata.

Two patterns are supported, tried in order:

1. **Inline `--swatch` CSS variable** — many themes render each Color option as
   `<tooltip-component ... style="--swatch: rgb(R G B);">` or
   `style="--swatch: url(...);">`. The hex / image URL is in the SSR'd HTML.

2. **External swatch JSON** (fallback when #1 yields nothing) — some themes
   (e.g. redaspenlove on Shopify) ship the color-name → hex mapping in a
   separate `swatches.json` file referenced from a JS config block as
   `swatches: '//host/path/swatches.json?v=...'`, and use JS at runtime to
   inject `--swatch` into the DOM. We read variant names from `data-swatch=`
   on the SSR'd `<radio-swatch>` elements and look up the hex codes in the
   external JSON ourselves — no JS execution needed.

Returns a list of dicts in option order:
    {"name": "Rose Gold", "kind": "url", "value": "https://.../glitz.jpg"}
    {"name": "Black",     "kind": "rgb", "value": "#000000"}

Notes:
- We do NOT execute JS; both paths only read the SSR'd HTML plus, for path 2,
  one extra GET to the external swatches.json file.
- `value` is normalized: rgb tuples -> "#RRGGBB"; url() -> absolute https URL.
- If neither pattern matches, returns []. Use --swatch-images as the manual
  fallback.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import List, Optional

# Capture every <tooltip-component ...> block on the PDP. Color swatches all
# carry data-tooltip="<ColorName>" and an inline --swatch CSS variable.
_TOOLTIP_RE = re.compile(
    r'<tooltip-component\b(?P<attrs>[^>]*?)>',
    re.IGNORECASE | re.DOTALL,
)
_DATA_TOOLTIP_RE = re.compile(r'data-tooltip="([^"]+)"', re.IGNORECASE)
_SWATCH_STYLE_RE = re.compile(
    r'--swatch:\s*([^;"\']+?)\s*(?:;|"|\'|$)',
    re.IGNORECASE,
)
_RGB_RE = re.compile(
    r'rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*\)',
    re.IGNORECASE,
)
_URL_RE = re.compile(r'url\(\s*["\']?([^"\')\s]+)["\']?\s*\)', re.IGNORECASE)

# External swatch JSON pattern: themes that inject --swatch at runtime ship the
# color name -> hex mapping in a separate file referenced in a JS config block.
_SWATCH_JSON_REF_RE = re.compile(
    r'''['"]?swatches['"]?\s*:\s*['"]([^'"]+swatches\.json[^'"]*)['"]''',
    re.IGNORECASE,
)
# Variant names from the SSR'd color option inputs.
# Themes vary: some emit `data-swatch="..."` on a <label>, others rely on the
# Shopify-standard `<input name="options[Color|Colour|...]" value="...">` which
# is always present. We try both patterns and de-dupe.
_OPTION_INPUT_NAME_RE = re.compile(
    r'<input\b[^>]*?\bname="options\[(?:Color|Colour|Shade|Color\s*Family|Colour\s*Family)\]"[^>]*?\bvalue="([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)
_DATA_SWATCH_ATTR_RE = re.compile(
    r'\bdata-swatch="([^"]+)"',
    re.IGNORECASE,
)


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    return body.decode("utf-8", errors="replace")


def _normalize_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("/"):
        # Relative to origin — caller knows the PDP URL but we don't here;
        # leave as-is and let the downloader fail noisily.
        return raw
    return raw


def parse_pdp_swatches(html: str) -> List[dict]:
    """Extract (color_name, kind, value) triples from a Shopify PDP HTML string."""
    out: List[dict] = []
    seen_names: set[str] = set()
    for match in _TOOLTIP_RE.finditer(html):
        attrs = match.group("attrs")
        name_m = _DATA_TOOLTIP_RE.search(attrs)
        style_m = _SWATCH_STYLE_RE.search(attrs)
        if not (name_m and style_m):
            continue
        name = name_m.group(1).strip()
        if name in seen_names:
            # Some themes render the same swatch twice (mobile + desktop).
            continue
        raw_value = style_m.group(1).strip()
        rgb_m = _RGB_RE.match(raw_value)
        url_m = _URL_RE.match(raw_value)
        if rgb_m:
            r, g, b = (int(rgb_m.group(i)) for i in (1, 2, 3))
            out.append({"name": name, "kind": "rgb",
                        "value": f"#{r:02X}{g:02X}{b:02X}"})
            seen_names.add(name)
        elif url_m:
            out.append({"name": name, "kind": "url",
                        "value": _normalize_url(url_m.group(1))})
            seen_names.add(name)
        # Else: unknown swatch CSS form — skip.
    return out


def parse_radio_swatch_names(html: str) -> List[str]:
    """Pull color-variant names from the SSR'd PDP in option order.

    Tries `<input name="options[Color]" value="...">` first (Shopify-standard,
    almost always present on color-option PDPs), then falls back to any
    `data-swatch="..."` attributes (used by some themes on <label>).

    De-dupes while preserving first-seen order (themes often render the swatch
    bar twice for mobile/desktop).
    """
    out: List[str] = []
    seen: set[str] = set()
    for pattern in (_OPTION_INPUT_NAME_RE, _DATA_SWATCH_ATTR_RE):
        for m in pattern.finditer(html):
            name = m.group(1).strip()
            if name and name not in seen:
                out.append(name)
                seen.add(name)
        if out:
            return out
    return out


def find_external_swatch_json_url(html: str, pdp_url: str) -> Optional[str]:
    """Locate the swatches.json URL referenced from a JS config block.

    Returns an absolute URL, or None if no reference is found. `pdp_url` is
    used to resolve protocol-relative or path-relative references.
    """
    m = _SWATCH_JSON_REF_RE.search(html)
    if not m:
        return None
    raw = m.group(1).strip()
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("http"):
        return raw
    return urllib.parse.urljoin(pdp_url, raw)


def fetch_external_swatch_json(url: str) -> dict:
    """Fetch + flatten a Shopify-style swatches.json into a lowercase-name -> value map.

    Tolerates two shapes:
      - {"colors": [{"Tulip": "#FF8BB3"}, {"Wisteria": "#F0AECD"}, ...]}
      - {"Tulip": "#FF8BB3", ...}  (flat dict)
    The value may be a hex string, an rgb() string, or a swatch image URL —
    we pass it through untouched and let the caller classify.
    """
    raw = json.loads(_fetch(url))
    flat: dict = {}
    if isinstance(raw, dict) and "colors" in raw and isinstance(raw["colors"], list):
        for entry in raw["colors"]:
            if isinstance(entry, dict):
                for k, v in entry.items():
                    flat[k.lower()] = v
    elif isinstance(raw, dict):
        for k, v in raw.items():
            flat[k.lower()] = v
    return flat


def _classify_swatch_value(value: str) -> Optional[dict]:
    """Turn a raw swatches.json value into a {kind, value} pair, or None to skip."""
    v = value.strip()
    if v.startswith("#") and (len(v) == 7 or len(v) == 4):
        # Normalize #rgb shorthand to #rrggbb upper.
        if len(v) == 4:
            v = "#" + "".join(c * 2 for c in v[1:])
        return {"kind": "rgb", "value": v.upper()}
    rgb_m = re.match(
        r'rgb\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)\s*\)', v, re.IGNORECASE)
    if rgb_m:
        r, g, b = (int(rgb_m.group(i)) for i in (1, 2, 3))
        return {"kind": "rgb", "value": f"#{r:02X}{g:02X}{b:02X}"}
    if v.startswith(("http://", "https://", "//")) or v.endswith(
            (".png", ".jpg", ".jpeg", ".svg", ".webp")):
        url = v if v.startswith("http") else (
            "https:" + v if v.startswith("//") else v)
        return {"kind": "url", "value": url}
    return None


def resolve_swatches_via_external_json(
    html: str, pdp_url: str,
) -> List[dict]:
    """Fallback path: derive {name, kind, value} list from <radio-swatch>
    variant names + external swatches.json.

    Returns [] if either the swatches.json reference or any matching name is
    missing (in which case the caller should fall back to CV extraction).
    """
    names = parse_radio_swatch_names(html)
    if not names:
        return []
    json_url = find_external_swatch_json_url(html, pdp_url)
    if not json_url:
        return []
    try:
        lookup = fetch_external_swatch_json(json_url)
    except Exception:
        return []

    out: List[dict] = []
    for name in names:
        raw = lookup.get(name.lower())
        if raw is None:
            # Unknown name — skip; downstream renderer will simply show fewer
            # swatches, which is still better than a wrong color.
            continue
        classified = _classify_swatch_value(str(raw))
        if classified is None:
            continue
        out.append({"name": name, **classified})
    return out


def fetch_pdp_swatches(pdp_url: str) -> List[dict]:
    """End-to-end: GET the PDP and parse it.

    Tries inline `--swatch` parsing first; falls back to the external
    swatches.json path if no inline swatches were found.
    """
    html = _fetch(pdp_url)
    inline = parse_pdp_swatches(html)
    if inline:
        return inline
    return resolve_swatches_via_external_json(html, pdp_url)


if __name__ == "__main__":
    import json
    import sys
    target = sys.argv[1]
    print(json.dumps(fetch_pdp_swatches(target), indent=2))
