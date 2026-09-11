"""
Color analyzer for product variant images.

Extracts the dominant garment color from a variant image, filtering out
the typical white/light product photo background.

Usage:
    from analyzer import extract_dominant_color, classify_variant
    hex_color = extract_dominant_color("variants/red_tshirt.jpg")
    info = classify_variant("variants/print_fabric.jpg")
    # -> {"hex": "#A37CB6", "is_pattern": True, "variance": 142.3}
"""
from PIL import Image
from collections import Counter
from typing import Optional
import statistics


def _load_and_shrink(image_path: str, max_side: int = 200) -> Image.Image:
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_side, max_side))
    return img


def _foreground_pixels(img: Image.Image, white_threshold: int = 235) -> list:
    """Return pixels that are NOT background (white/very light)."""
    pixels = list(img.getdata())
    return [p for p in pixels if not all(c >= white_threshold for c in p)]


def extract_dominant_color(image_path: str) -> str:
    """
    Returns hex string like '#A1795B'. Filters out white-ish background,
    buckets remaining pixels by 16-step grid, then averages the top bucket
    for a smoother color than picking a single pixel.
    """
    img = _load_and_shrink(image_path)
    fg = _foreground_pixels(img)
    if not fg:
        return "#FFFFFF"

    buckets: Counter = Counter()
    for r, g, b in fg:
        buckets[(r // 16, g // 16, b // 16)] += 1
    top = buckets.most_common(1)[0][0]

    matching = [
        p for p in fg
        if (p[0] // 16, p[1] // 16, p[2] // 16) == top
    ]
    avg = tuple(sum(p[i] for p in matching) // len(matching) for i in range(3))
    return "#{:02X}{:02X}{:02X}".format(*avg)


def variance_score(image_path: str) -> float:
    """
    Returns the spread of foreground colors. Solid colors -> low (~10-30),
    prints/patterns -> high (>80). Used to detect 'pattern' variants where
    a single color swatch would misrepresent the product.
    """
    img = _load_and_shrink(image_path)
    fg = _foreground_pixels(img)
    if len(fg) < 10:
        return 0.0
    return statistics.pstdev([sum(p) / 3 for p in fg])


def classify_variant(image_path: str) -> dict:
    """
    Full analysis: dominant color + pattern detection.
    
    Returns:
        {
            "hex": "#A1795B",
            "variance": 23.5,
            "is_pattern": False,
        }
    """
    hex_color = extract_dominant_color(image_path)
    variance = variance_score(image_path)
    # Two-signal pattern detection:
    #  - color spread (variance) is above noise floor
    #  - top color bucket covers <50% of foreground (multi-hue)
    img = _load_and_shrink(image_path)
    fg = _foreground_pixels(img)
    if fg:
        buckets: Counter = Counter()
        for r, g, b in fg:
            buckets[(r // 16, g // 16, b // 16)] += 1
        top_share = buckets.most_common(1)[0][1] / len(fg)
    else:
        top_share = 1.0
    is_pattern = (variance > 28.0) and (top_share < 0.5)
    return {
        "hex": hex_color,
        "variance": round(variance, 1),
        "is_pattern": is_pattern,
    }


if __name__ == "__main__":
    import sys
    for path in sys.argv[1:]:
        print(f"{path}: {classify_variant(path)}")
