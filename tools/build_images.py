"""Export hero and application photos to responsive AVIF + WebP.

Sources are either linked files in koppelingen/ or a clipped render of a page
in bw huisstijl.ai (for mockups whose logo is placed as vector on top).

Usage: python tools/build_images.py  (needs pymupdf + pillow with avif)
"""
from pathlib import Path

import fitz
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "nieuwe huisstijl 2026"
AI = SRC / "bw huisstijl.ai"
LINKS = SRC / "koppelingen"
OUT = ROOT / "branding" / "assets" / "img"

# name: (source, widths)
# source = filename in koppelingen/ or ("ai", page number, clip rect in pt)
IMAGES = {
    "hero": ("bw vanboven.png", [640, 960, 1440, 1920, 2528]),
    "story": ("side bw.png", [640, 960, 1440]),
    "app-shirt": ("Gemini_Generated_Image_hwl37ehwl37ehwl3.png", [480, 800, 1200]),
    "app-flag-lime": (("ai", 20, (65, 127, 294, 468)), [400, 640, 960]),
    "app-flag-asphalt": (("ai", 20, (307, 127, 534, 468)), [400, 640, 960]),
    "app-flag-baseline": (("ai", 20, (547, 127, 777, 468)), [400, 640, 960]),
    "app-facade": (("ai", 28, (424, 151, 807, 461)), [640, 1024, 1600]),
    "app-cards": ("Business_Card_Mockup_3.png", [640, 1024, 1600]),
    "app-plate": ("bw plaatje.png", [480, 800, 1200]),
    "app-trailer": ("remorque new logo.png", [640, 1024, 1600]),
}


def load(source):
    if isinstance(source, str):
        im = Image.open(LINKS / source)
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, "white")
            im = im.convert("RGBA")
            bg.paste(im, mask=im.getchannel("A"))
            return bg
        return im.convert("RGB")
    _, page_no, rect = source
    doc = fitz.open(AI)
    clip = fitz.Rect(rect)
    zoom = min(2400 / clip.width, 1600 / clip.height)
    pix = doc[page_no - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (source, widths) in IMAGES.items():
        im = load(source)
        for w in widths:
            w = min(w, im.width)
            h = round(im.height * w / im.width)
            resized = im.resize((w, h), Image.LANCZOS)
            resized.save(OUT / f"{name}-{w}.webp", quality=80, method=6)
            resized.save(OUT / f"{name}-{w}.avif", quality=55)
        print(f"{name}: {im.width}x{im.height} -> {widths}")


if __name__ == "__main__":
    main()
