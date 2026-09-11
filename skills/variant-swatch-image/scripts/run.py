"""
CLI entry point for variant-swatch-image.

Renders the six fixed layouts (see scripts/layouts.py) for one product.

Mode A — explicit paths:
    python scripts/run.py \\
        --main-image main.jpg \\
        --variants v1.jpg v2.jpg v3.jpg \\
        --output-dir ./out

Mode B — from Shopify products.json:
    python scripts/run.py \\
        --shopify-url https://store.com/products/handle \\
        --main-color carmine \\
        --output-dir ./out

The main image comes from the variant whose option1 matches --main-color
(or the first variant if not specified).

By default all six layouts are emitted; pass --layouts to subset:
    --layouts bare-bl-square,pill-br-h

Swatch source:
    By default, swatch glyphs come from CV-extracted colors of the variant
    images. To use the variant images themselves (rendered as circular/square
    image swatches), either:
      - Mode B: when variant.featured_image is populated in products.json,
        the image is used directly as the swatch — no flag needed.
      - Any mode: pass --swatch-images URL_OR_PATH ... to override with
        an explicit list of swatch images (URLs are downloaded). This wins
        over both auto-detection and color extraction.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from analyzer import classify_variant
from layouts import DEFAULT_LAYOUT_IDS
from renderer import render_layouts
from shopify_pdp import fetch_pdp_swatches


def _download(url: str, dest: Path) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dest.write_bytes(resp.read())
    return dest


def _ensure_local(path_or_url: str, work_dir: Path, name: str) -> Path:
    """Return a local Path for either a URL or an existing local path."""
    if path_or_url.startswith(("http://", "https://")):
        ext = Path(path_or_url.split("?", 1)[0]).suffix or ".jpg"
        dest = work_dir / f"{name}{ext}"
        return _download(path_or_url, dest)
    if path_or_url.startswith("//"):
        return _ensure_local("https:" + path_or_url, work_dir, name)
    p = Path(path_or_url)
    if not p.exists():
        raise FileNotFoundError(p)
    return p


def _shopify_products_json(product_url: str) -> dict:
    if product_url.endswith("/"):
        product_url = product_url[:-1]
    json_url = product_url + ".json"
    req = urllib.request.Request(json_url,
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _resolve_from_shopify(
    product_url: str,
    main_color: Optional[str],
    work_dir: Path,
) -> tuple[Path, list[tuple[Path, bool]]]:
    """
    Returns (main_image_path, [(variant_image_path, has_featured_image)]).

    `has_featured_image` records whether this variant exposed its own
    featured_image in products.json — when True the caller will treat that
    image as the swatch directly; when False, color extraction is used.

    With current Shopify products.json schema, every downloaded variant image
    *is* a featured_image, so the flag is True for every entry here. The
    flag stays in the signature for parity with future per-variant heuristics.
    """
    data = _shopify_products_json(product_url)
    product = data.get("product", data)
    variants = product["variants"]
    images = {img["id"]: img["src"] for img in product.get("images", [])}

    entries: list[tuple[Path, bool]] = []
    main_idx = 0
    for i, v in enumerate(variants):
        color_name = (v.get("option1") or "").lower()
        if main_color and color_name == main_color.lower():
            main_idx = i
        fi = v.get("featured_image") or {}
        img_id = fi.get("id")
        src = images.get(img_id) or fi.get("src")
        if not src:
            continue
        if not src.startswith("http"):
            src = "https:" + src
        local = work_dir / f"variant_{i}_{color_name or 'unnamed'}.jpg"
        _download(src, local)
        entries.append((local, True))

    main_fi = variants[main_idx].get("featured_image") or {}
    main_src = main_fi.get("src")
    if not main_src:
        # Fallback: variant has no featured_image — use the product's first image.
        product_images = product.get("images", [])
        if product_images:
            main_src = product_images[0]["src"]
    if not main_src:
        raise RuntimeError("No image found for the selected variant or product")
    if not main_src.startswith("http"):
        main_src = "https:" + main_src
    main_local = work_dir / "main.jpg"
    _download(main_src, main_local)
    return main_local, entries


def _build_swatches(
    variant_entries: list[tuple[str, bool]],
) -> list[dict]:
    """
    variant_entries: list of (path, prefer_image_swatch).
    - prefer_image_swatch=True -> use the image directly as swatch (center-cropped).
    - prefer_image_swatch=False -> CV-extract: pattern -> image swatch, else color.
    """
    swatches = []
    for vpath, prefer_image in variant_entries:
        if prefer_image:
            swatches.append({"image_path": vpath})
            continue
        info = classify_variant(vpath)
        if info["is_pattern"]:
            swatches.append({"image_path": vpath})
        else:
            swatches.append({"color": info["hex"]})
    return swatches


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--main-image", help="Path to merchant's main product image (Mode A)")
    p.add_argument("--variants", nargs="+",
                   help="Paths to variant images (Mode A)")

    p.add_argument("--shopify-url",
                   help="Shopify product URL — auto-fetches via products.json (Mode B)")
    p.add_argument("--main-color",
                   help="Color option1 value whose image is used as the main image (Mode B)")

    p.add_argument("--pdp-url",
                   help="Shopify PDP URL — scrapes inline option-swatch metadata "
                        "(rgb() or url()) authored by the merchant. Mode C. "
                        "Combine with --shopify-url for the main product image, "
                        "or pass --main-image directly.")

    p.add_argument("--swatch-images", nargs="+",
                   help="Explicit swatch images (URLs or local paths). When set, "
                        "overrides auto-detection and CV color extraction.")

    p.add_argument("--output-dir", "-o", required=True,
                   help="Directory to save rendered PNGs ({layout_id}.png each).")
    p.add_argument("--bg-color", default="#FFFFFF",
                   help="Product area background hex (default: white)")
    p.add_argument("--layouts",
                   help=f"Comma-separated layout IDs. Default: all six "
                        f"({','.join(DEFAULT_LAYOUT_IDS)})")

    args = p.parse_args()
    layout_ids = args.layouts.split(",") if args.layouts else None

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Resolve main image + auto variants.
        if args.shopify_url:
            main_image, auto_entries = _resolve_from_shopify(
                args.shopify_url, args.main_color, tmp_path)
            print(f"Fetched {len(auto_entries)} variants from {args.shopify_url}")
        elif args.main_image:
            main_image = Path(args.main_image)
            auto_entries = []
            if args.variants:
                auto_entries = [(Path(v), False) for v in args.variants]
        elif args.pdp_url:
            # PDP-only mode: derive products.json URL from the PDP URL so we
            # can still grab the main image.
            base = args.pdp_url.split("?", 1)[0].rstrip("/")
            main_image, auto_entries = _resolve_from_shopify(
                base, args.main_color, tmp_path)
            print(f"Fetched main image via {base}.json")
        else:
            p.error("Need --shopify-url, --main-image (+--variants/--swatch-images), "
                    "or --pdp-url")
            return

        # Build swatches. Precedence: --swatch-images > --pdp-url > auto_entries.
        if args.swatch_images:
            entries = []
            for idx, raw in enumerate(args.swatch_images):
                local = _ensure_local(raw, tmp_path, f"swatch_{idx}")
                entries.append((str(local), True))
            swatches = _build_swatches(entries)
        elif args.pdp_url:
            parsed = fetch_pdp_swatches(args.pdp_url)
            print(f"Parsed {len(parsed)} option swatches from PDP")
            swatches = []
            for idx, sw in enumerate(parsed):
                if sw["kind"] == "rgb":
                    swatches.append({"color": sw["value"]})
                elif sw["kind"] == "url":
                    local = _ensure_local(
                        sw["value"], tmp_path, f"pdp_swatch_{idx}")
                    swatches.append({"image_path": str(local)})
        else:
            entries = [(str(p), flag) for p, flag in auto_entries]
            swatches = _build_swatches(entries)

        if not swatches:
            sys.exit("No swatches resolved. Pass --variants, --swatch-images, "
                     "or use a Shopify URL/PDP that exposes variants.")

        results = render_layouts(
            main_image_path=str(main_image),
            swatches=swatches,
            layouts=layout_ids,
            output_dir=args.output_dir,
            bg_color=args.bg_color,
        )

    for r in results:
        print(f"[{r['layout']:16s}] {r['url']}")
        if r["local_path"]:
            print(f"  -> {r['local_path']}")


if __name__ == "__main__":
    main()
