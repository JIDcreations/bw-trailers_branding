"""Extract the BW logo from the brand book (.ai, page 10) and export SVG, PNG and JPG variants.

The mark (B, W and the oval ring) is stored as vector paths in the .ai.
The baseline "trailers, built for you." is live Michroma text; it is converted
to outlines here so the SVG does not depend on the font being installed.

Usage: python tools/extract_logos.py  (needs pymupdf + fonttools)
"""
from pathlib import Path

import fitz
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
SRC_AI = ROOT / "nieuwe huisstijl 2026" / "bw huisstijl.ai"
SRC_FONT = ROOT / "nieuwe huisstijl 2026" / "fonts" / "Michroma-Regular.ttf"
OUT = ROOT / "branding" / "assets" / "logos"

PAGE = 9            # page 10: lime logo on asphalt (left half)
SCALE = 4           # pt -> svg units, keeps coordinates readable
PNG_WIDTH = 2400
JPG_WIDTH = 2400

# Colours as specified in bw huisstijl.ai (page 14)
COLORS = {
    "lime": "#a3be42",
    "asphalt": "#2f2b3d",
    "white": "#ffffff",
    "black": "#000000",
}
# JPG has no transparency: each colour gets a background it is allowed on
JPG_BACKGROUND = {
    "lime": "#2f2b3d",
    "asphalt": "#ffffff",
    "white": "#2f2b3d",
    "black": "#ffffff",
}


def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def drawing_to_d(drawing, ox, oy):
    """Convert a PyMuPDF drawing to an SVG path string, relative to (ox, oy)."""
    def pt(p):
        return f"{fmt((p.x - ox) * SCALE)} {fmt((p.y - oy) * SCALE)}"

    parts, last = [], None
    for item in drawing["items"]:
        kind = item[0]
        if kind == "l":
            p1, p2 = item[1], item[2]
            if last is None or abs(p1 - last) > 0.01:
                parts.append(f"Z M{pt(p1)}" if parts else f"M{pt(p1)}")
            parts.append(f"L{pt(p2)}")
            last = p2
        elif kind == "c":
            p1, c1, c2, p2 = item[1:5]
            if last is None or abs(p1 - last) > 0.01:
                parts.append(f"Z M{pt(p1)}" if parts else f"M{pt(p1)}")
            parts.append(f"C{pt(c1)} {pt(c2)} {pt(p2)}")
            last = p2
        else:
            raise ValueError(f"unexpected path item {kind}")
    parts.append("Z")
    return " ".join(parts)


def baseline_to_d(span, ox, oy):
    """Outline the baseline text glyph by glyph, using the exact char origins from the .ai."""
    font = TTFont(SRC_FONT)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    k = span["size"] / font["head"].unitsPerEm
    paths = []
    for ch in span["chars"]:
        if ch["c"].isspace():
            continue
        x0, y0 = ch["origin"]
        pen = SVGPathPen(glyphs, ntos=fmt)
        # font units (y up) -> page points (y down) -> svg units
        tx = ((x0 - ox) * SCALE, (y0 - oy) * SCALE)
        glyphs[cmap[ord(ch["c"])]].draw(TransformPen(pen, (k * SCALE, 0, 0, -k * SCALE, *tx)))
        paths.append(pen.getCommands())
    return " ".join(paths)


def svg_doc(width, height, paths, color, title, background=None, pad=0):
    w, h = width + 2 * pad, height + 2 * pad
    bg = f'<rect width="{fmt(w)}" height="{fmt(h)}" fill="{background}"/>' if background else ""
    group = f'<g transform="translate({fmt(pad)} {fmt(pad)})" fill="{color}" fill-rule="evenodd">'
    body = "".join(f'<path d="{d}"/>' for d in paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(w)} {fmt(h)}" '
        f'width="{fmt(w / SCALE)}pt" height="{fmt(h / SCALE)}pt" role="img">'
        f"<title>{title}</title>{bg}{group}{body}</g></svg>\n"
    )


def render(svg, width, jpg_path=None, png_path=None):
    doc = fitz.open(stream=svg.encode(), filetype="svg")
    page = doc[0]
    zoom = width / page.rect.width
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=png_path is not None)
    if png_path:
        pix.save(png_path)
    if jpg_path:
        pix.save(jpg_path, jpg_quality=92)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(SRC_AI)
    page = doc[PAGE]
    drawings = page.get_drawings()
    # paths 2-4 are B, W and the ring of the left (lime) logo
    mark = drawings[2:5]
    ring = mark[2]["rect"]
    ox, oy = ring.x0, ring.y0
    mark_paths = [drawing_to_d(d, ox, oy) for d in mark]

    span = next(
        s
        for b in page.get_text("rawdict")["blocks"]
        for l in b.get("lines", [])
        for s in l["spans"]
        if s["origin"][0] < page.rect.width / 2
    )
    tag_path = baseline_to_d(span, ox, oy)
    tag_bottom = max(ring.y1, span["bbox"][3])
    tag_right = max(ring.x1, span["bbox"][2])

    # Clear space = height of the "B" (cap height of the mark)
    clear = mark[0]["rect"].height * SCALE

    sizes = {
        "mark": (ring.width * SCALE, ring.height * SCALE, mark_paths, "BW"),
        "logo": ((tag_right - ox) * SCALE, (tag_bottom - oy) * SCALE,
                 mark_paths + [tag_path], "BW – trailers, built for you."),
    }

    for kind, (w, h, paths, title) in sizes.items():
        for name, color in COLORS.items():
            base = OUT / f"bw-trailers-{kind}-{name}"
            svg = svg_doc(w, h, paths, color, title)
            base.with_suffix(".svg").write_text(svg)
            render(svg, PNG_WIDTH, png_path=str(base.with_suffix(".png")))
            jpg_svg = svg_doc(w, h, paths, color, title, background=JPG_BACKGROUND[name], pad=clear)
            render(jpg_svg, JPG_WIDTH, jpg_path=str(base.with_suffix(".jpg")))
            print("wrote", base.name)

    print(f"clear space: {clear / SCALE:.1f} pt = {clear / (ring.height * SCALE):.3f} x mark height")


if __name__ == "__main__":
    main()
