"""Build the branding page and the brand package from one copy file.

    python3 tools/build.py            # Dutch (default)
    python3 tools/build.py fr         # uses src/copy/fr.json -> fr/index.html

Output goes to branding/ (the only folder Netlify publishes).
All text lives in src/copy/<lang>.json. The template uses:
  {{key.path}}          copy text (HTML-escaped)
  {{pic:name}}          responsive <picture> (see PICTURES)
  {{srcset:name:fmt}}   srcset string only
  {{svg:name|class}}    inline SVG from assets/logos (decorative)
  {{dim:name}}          width/height attributes of a logo SVG
  {{variants}}          logo download cards
  {{zip.*}}             brand package link, name and size
Stdlib only, no dependencies.
"""
import html
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "branding"          # published folder (Netlify)
SRC = ROOT / "src"
ASSETS = BASE / "assets"
LOGOS = ASSETS / "logos"
IMG = ASSETS / "img"
FONT_EXTRA = SRC / "package-fonts"

# name: (sizes attribute, alt copy key, eager?)
PICTURES = {
    "hero": ("100vw", "hero.image_alt", True),
    "story": ("(min-width: 60em) 45vw, 100vw", "story.image_alt", False),
    "app-shirt": ("(min-width: 60em) 38vw, 100vw", "applications.shirt_alt", False),
    "app-facade": ("(min-width: 60em) 55vw, 100vw", "applications.facade_alt", False),
    "app-cards": ("(min-width: 60em) 55vw, 100vw", "applications.cards_alt", False),
    "app-flag-lime": ("(min-width: 60em) 30vw, 33vw", "applications.flag_lime_alt", False),
    "app-flag-asphalt": ("(min-width: 60em) 30vw, 33vw", "applications.flag_asphalt_alt", False),
    "app-flag-baseline": ("(min-width: 60em) 30vw, 33vw", "applications.flag_baseline_alt", False),
    "app-trailer": ("(min-width: 60em) 55vw, 100vw", "applications.trailer_alt", False),
    "app-plate": ("(min-width: 60em) 38vw, 100vw", "applications.plate_alt", False),
}

VARIANTS = ["lime", "asphalt", "white", "black"]
FORMATS = ["svg", "png", "jpg"]
ZIP_NAME = "bw-trailers-huisstijl.zip"


def lookup(copy, key):
    node = copy
    for part in key.split("."):
        node = node[part]
    return node


def esc(text):
    return html.escape(str(text), quote=True)


def image_widths(name):
    widths = sorted(int(p.stem.rsplit("-", 1)[1]) for p in IMG.glob(f"{name}-*.webp"))
    if not widths:
        raise SystemExit(f"no images for {name}; run tools/build_images.py")
    return widths


def image_size(name, width):
    """Read width/height from a WebP header (VP8/VP8L/VP8X) without Pillow."""
    data = (IMG / f"{name}-{width}.webp").read_bytes()[:40]
    chunk = data[12:16]
    if chunk == b"VP8X":
        w = 1 + int.from_bytes(data[24:27], "little")
        h = 1 + int.from_bytes(data[27:30], "little")
    elif chunk == b"VP8L":
        b = int.from_bytes(data[21:25], "little")
        w, h = (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    else:
        w = int.from_bytes(data[26:28], "little") & 0x3FFF
        h = int.from_bytes(data[28:30], "little") & 0x3FFF
    return w, h


def srcset(name, fmt):
    return ", ".join(f"assets/img/{name}-{w}.{fmt} {w}w" for w in image_widths(name))


def picture(copy, name):
    sizes, alt_key, eager = PICTURES[name]
    widths = image_widths(name)
    w, h = image_size(name, widths[-1])
    fallback = widths[min(1, len(widths) - 1)]
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (
        f'<picture class="pic pic--{name}">'
        f'<source type="image/avif" srcset="{srcset(name, "avif")}" sizes="{sizes}">'
        f'<source type="image/webp" srcset="{srcset(name, "webp")}" sizes="{sizes}">'
        f'<img src="assets/img/{name}-{fallback}.webp" alt="{esc(lookup(copy, alt_key))}" '
        f'width="{w}" height="{h}" {loading}>'
        f"</picture>"
    )


def svg_viewbox(name):
    svg = (LOGOS / f"{name}.svg").read_text()
    _, _, w, h = re.search(r'viewBox="([^"]+)"', svg).group(1).split()
    return svg, round(float(w)), round(float(h))


def inline_svg(name, cls):
    if name == "download-icon":
        return (
            f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<path d="M12 3v12m0 0l-5-5m5 5l5-5M4 20h16" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        )
    svg, _, _ = svg_viewbox(name)
    svg = re.sub(r'\s(width|height)="[^"]+"', "", svg, count=2)
    svg = svg.replace('role="img"', f'class="{cls}" aria-hidden="true" focusable="false"')
    svg = re.sub(r"<title>.*?</title>", "", svg)
    return svg.strip()


def variants(copy):
    d = copy["downloads"]
    items = []
    for v in VARIANTS:
        name = d[f"variant_{v}"]
        links = []
        for fmt in FORMATS:
            logo = f"bw-trailers-logo-{v}.{fmt}"
            mark = f"bw-trailers-mark-{v}.{fmt}"
            links.append(
                f'<li><a class="fmt" href="assets/logos/{logo}" download="{logo}" '
                f'data-logo="{logo}" data-mark="{mark}">'
                f'<span class="visually-hidden">{esc(d["download"])} {esc(name)}, </span>{fmt.upper()}</a></li>'
            )
        _, w, h = svg_viewbox(f"bw-trailers-logo-{v}")
        items.append(
            f'<li class="variant variant--{v}">'
            f'<div class="variant__preview">'
            f'<img src="assets/logos/bw-trailers-logo-{v}.svg" width="{w}" height="{h}" loading="lazy" '
            f'alt="{esc(d["alt_logo"])} {esc(name)}" '
            f'data-logo="bw-trailers-logo-{v}.svg" data-mark="bw-trailers-mark-{v}.svg" '
            f'data-alt-logo="{esc(d["alt_logo"])} {esc(name)}" data-alt-mark="{esc(d["alt_mark"])} {esc(name)}">'
            f"</div>"
            f'<div class="variant__body"><h3 class="variant__name">{esc(name)}</h3>'
            f'<p class="variant__use">{esc(d[f"variant_{v}_use"])}</p>'
            f'<ul class="formats">{"".join(links)}</ul></div></li>'
        )
    return "\n          ".join(items)


def build_zip(copy, out_dir):
    """Logos, fonts (+ licences) and a readme in one archive."""
    path = out_dir / ZIP_NAME
    top = "bw-trailers-huisstijl"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{top}/{copy['package']['readme_name']}", "\n".join(copy["package"]["readme"]) + "\n")
        for fmt in FORMATS:
            for f in sorted(LOGOS.glob(f"*.{fmt}")):
                z.write(f, f"{top}/logo/{fmt}/{f.name}")
        z.write(FONT_EXTRA / "Michroma-Regular.ttf", f"{top}/fonts/Michroma/Michroma-Regular.ttf")
        z.write(FONT_EXTRA / "Michroma-OFL.txt", f"{top}/fonts/Michroma/OFL.txt")
        for f in ["Lato-Regular.ttf", "Lato-Bold.ttf"]:
            z.write(FONT_EXTRA / f, f"{top}/fonts/Lato/{f}")
        z.write(FONT_EXTRA / "Lato-OFL.txt", f"{top}/fonts/Lato/OFL.txt")
    return path


def human_size(n):
    return f"{n / 1_000_000:.1f} MB".replace(".", ",") if n >= 1_000_000 else f"{round(n / 1000)} kB"


def main():
    lang = sys.argv[1] if len(sys.argv) > 1 else "nl"
    copy = json.loads((SRC / "copy" / f"{lang}.json").read_text())
    template = (SRC / "template.html").read_text()

    # Dutch lives at the root of /branding/, other languages in a subfolder
    out_dir = BASE if lang == "nl" else BASE / lang
    prefix = "" if lang == "nl" else "../"
    out_dir.mkdir(exist_ok=True)

    zip_path = build_zip(copy, BASE)
    zip_info = {
        "href": f"{prefix}{ZIP_NAME}",
        "name": ZIP_NAME,
        "meta": copy["package"]["meta"].replace("{size}", human_size(zip_path.stat().st_size)),
    }

    def replace(match):
        token = match.group(1).strip()
        if token.startswith("pic:"):
            return picture(copy, token[4:])
        if token.startswith("srcset:"):
            _, name, fmt = token.split(":")
            return srcset(name, fmt)
        if token.startswith("svg:"):
            name, cls = token[4:].split("|")
            return inline_svg(name, cls)
        if token.startswith("dim:"):
            _, w, h = svg_viewbox(token[4:])
            return f'width="{w}" height="{h}"'
        if token == "variants":
            return variants(copy)
        if token.startswith("zip."):
            return esc(zip_info[token[4:]])
        return esc(lookup(copy, token))

    page = re.sub(r"\{\{(.+?)\}\}", replace, template)
    if prefix:
        page = page.replace('"assets/', f'"{prefix}assets/').replace(" assets/", f" {prefix}assets/")
    (out_dir / "index.html").write_text(page)
    print(f"wrote {out_dir / 'index.html'} and {zip_path.name} ({human_size(zip_path.stat().st_size)})")


if __name__ == "__main__":
    main()
